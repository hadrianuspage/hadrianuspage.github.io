<?php

namespace App\Services\Amf;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class RedeemTicket
{
    protected int $regenInterval = 1200; // default 20 minutes in seconds
    protected int $maxTickets = 6; // default cap
    protected bool $notifyOnCap = true;

    protected string $cachePrefix = 'redeem_tickets:'; // cache key per char
    protected string $petHistoryPrefix = 'redeem_pet_history:'; // key to store recent awarded pets per char
    protected string $configKey = 'redeem_ticket_items';
    protected string $settingsKey = 'redeem_ticket_settings';
    protected string $notifyPrefix = 'redeem_tickets_notify:'; // notify cache key

    public function getData($params)
    {
        $args = $this->normalizeParams($params);
        $charId = $args[0] ?? null;
        if (!$charId) {
            return ['status' => 0, 'error' => 1, 'result' => 'Invalid params'];
        }

        $this->loadSettings();

        $ticketState = $this->loadTicketState($charId);
        $ticketState = $this->applyRegen($ticketState, $charId);
        $this->saveTicketState($charId, $ticketState);

        $exchanges = $this->loadExchangesConfig();

        return [
            'status' => 1,
            'error' => 0,
            'tickets' => (int)$ticketState['tickets'],
            'cap_reached' => ((int)$ticketState['tickets'] >= $this->maxTickets),
            'exchanges' => $exchanges,
        ];
    }

    public function exchange($params)
    {
        $args = $this->normalizeParams($params);
        $charId = $args[0] ?? null;
        $session = $args[1] ?? null;
        $code = $args[2] ?? null;
        $count = isset($args[3]) ? (int)$args[3] : 1;
        if (!$charId || !$code) {
            return ['status' => 0, 'error' => 1, 'result' => 'Invalid params'];
        }
        if ($count < 1) $count = 1;

        $this->loadSettings();

        $ticketState = $this->loadTicketState($charId);
        $ticketState = $this->applyRegen($ticketState, $charId);

        if ((int)$ticketState['tickets'] < $count) {
            return ['status' => 2, 'error' => 0, 'result' => 'You do not have enough tickets.'];
        }

        $exchanges = $this->loadExchangesConfig();
        $cfg = null;
        foreach ($exchanges as $e) {
            if (($e['code'] ?? '') === $code) { $cfg = $e; break; }
        }
        if (!$cfg) {
            return ['status' => 0, 'error' => 1, 'result' => 'Unknown exchange code'];
        }

        // Deduct tickets and save
        $ticketState['tickets'] = max(0, (int)$ticketState['tickets'] - $count);
        $this->saveTicketState($charId, $ticketState);

        $applied = [];
        try {
            $character = DB::table('characters')->where('id', $charId)->first();
            if (!$character) {
                return ['status' => 0, 'error' => 1, 'result' => 'Character not found'];
            }
            $user = DB::table('users')->where('id', $character->user_id)->first();

            for ($i = 0; $i < $count; $i++) {
                $this->applyExchangeConfig($character, $user, $cfg, $applied);
            }
        } catch (\Throwable $e) {
            Log::error('RedeemTicket.exchange apply error: '.$e->getMessage(), ['exception'=>$e]);
            return ['status' => 0, 'error' => 1, 'result' => 'Exchange failed'];
        }

        return ['status' => 1, 'error' => 0, 'result' => 'Exchange success', 'applied' => $applied];
    }

    protected function normalizeParams($params): array
    {
        if (is_array($params) && isset($params[0]) && is_array($params[0])) {
            return $params[0];
        }
        if (is_array($params)) return $params;
        return [];
    }

    protected function loadSettings(): void
    {
        try {
            $row = DB::table('game_configs')->where('key', $this->settingsKey)->first();
            if ($row && !empty($row->value)) {
                $cfg = json_decode($row->value, true);
                if (is_array($cfg)) {
                    if (!empty($cfg['regen_interval']) && is_numeric($cfg['regen_interval'])) {
                        $this->regenInterval = (int)$cfg['regen_interval'];
                    }
                    if (!empty($cfg['max_tickets']) && is_numeric($cfg['max_tickets'])) {
                        $this->maxTickets = max(1, (int)$cfg['max_tickets']);
                    }
                    if (isset($cfg['notify_on_cap'])) {
                        $this->notifyOnCap = (bool)$cfg['notify_on_cap'];
                    }
                }
            }
        } catch (\Throwable $e) {
            Log::error('loadSettings error: '.$e->getMessage());
        }
    }

    protected function loadExchangesConfig(): array
    {
        try {
            $row = DB::table('game_configs')->where('key', $this->configKey)->first();
            if ($row) {
                $value = json_decode($row->value, true);
                if (is_array($value)) return $value;
            }
        } catch (\Throwable $e) {
            Log::error('loadExchangesConfig error: '.$e->getMessage());
        }

        return [
            ['qty'=>500,'code'=>'tokens','type'=>'tokens'],
            ['qty'=>500000,'code'=>'gold','type'=>'gold'],
            ['qty'=>50,'code'=>'onigiri','type'=>'item'],
            ['qty'=>30,'code'=>'golden_stamina_roll','type'=>'item'],
            ['qty'=>30,'code'=>'vitality_gourd','type'=>'item'],
            ['qty'=>500,'code'=>'tp','type'=>'tp'],
            ['qty'=>10000,'code'=>'prestige','type'=>'prestige'],
            ['qty'=>10000,'code'=>'merit','type'=>'merit'],
            ['qty'=>100,'code'=>'friendship_kunai','type'=>'item'],
            ['qty'=>200,'code'=>'pvp_coin','type'=>'pvp_coin'],
            ['qty'=>20,'code'=>'moyai','type'=>'item'],
            ['qty'=>300,'code'=>'ss','type'=>'ss'],
            ['qty'=>2,'code'=>'dragon_ball','type'=>'dragon_ball'],
            ['qty'=>1,'code'=>'pet','type'=>'pet','swf'=>'pet_hachibi','pool'=>[
                'pet_jyubi','pet_kyubi','pet_hachibi','pet_nanabi','pet_rokubi','pet_gobi','pet_yobi','pet_sanbi','pet_nibi','pet_ichibi'
            ], 'expiry'=>'6 days']
        ];
    }

    protected function loadTicketState(int $charId): array
    {
        $key = $this->cachePrefix.$charId;
        $row = $this->readCacheRow($key);
        if (!$row) {
            $now = time();
            $state = ['tickets' => 1, 'last' => $now];
            $this->writeCacheRow($key, $state, 60*60*24*30);
            return $state;
        }
        $row['tickets'] = min($this->maxTickets, (int)($row['tickets'] ?? 0));
        $row['last'] = (int)($row['last'] ?? time());
        return $row;
    }

    protected function saveTicketState(int $charId, array $state)
    {
        $state['tickets'] = min($this->maxTickets, (int)($state['tickets'] ?? 0));
        $key = $this->cachePrefix.$charId;
        $this->writeCacheRow($key, $state, 60*60*24*30);
    }

    protected function applyRegen(array $state, int $charId): array
    {
        $now = time();
        $last = (int)($state['last'] ?? $now);
        $current = (int)($state['tickets'] ?? 0);

        if ($current >= $this->maxTickets) {
            return $state;
        }

        if ($now <= $last) return $state;

        $delta = $now - $last;
        $intervals = intdiv($delta, $this->regenInterval);
        if ($intervals <= 0) return $state;

        $space = $this->maxTickets - $current;
        $add = min($intervals, $space);
        if ($add <= 0) return $state;

        $prior = $current;
        $state['tickets'] = $current + $add;
        $state['last'] = $last + $add * $this->regenInterval;

        if ($this->notifyOnCap && $state['tickets'] >= $this->maxTickets && $prior < $this->maxTickets) {
            // reached cap now
            $this->notifyCapReached($charId);
        }

        return $state;
    }

    protected function notifyCapReached(int $charId): void
    {
        try {
            $key = $this->notifyPrefix.$charId;
            $payload = ['notified_at' => time(), 'max_tickets' => $this->maxTickets];
            $this->writeCacheRow($key, $payload, 60*60*24*7); // keep a week
            Log::info('RedeemTicket: tickets cap reached', ['charId' => $charId, 'max' => $this->maxTickets]);
        } catch (\Throwable $e) {
            Log::error('notifyCapReached failed: '.$e->getMessage(), ['charId' => $charId]);
        }
    }

    protected function applyExchangeConfig($character, $user, $cfg, array &$applied)
    {
        $type = $cfg['type'] ?? ($cfg['code'] ?? null);
        $qty = (int)($cfg['qty'] ?? 1);

        switch ($type) {
            case 'tokens':
                if ($user) {
                    DB::table('users')->where('id', $user->id)->increment('tokens', $qty);
                    $applied[] = ['type'=>'tokens','amount'=>$qty];
                }
                break;
            case 'gold':
                DB::table('characters')->where('id', $character->id)->increment('gold', $qty);
                $applied[] = ['type'=>'gold','amount'=>$qty];
                break;
            case 'tp':
                DB::table('characters')->where('id', $character->id)->increment('tp', $qty);
                $applied[] = ['type'=>'tp','amount'=>$qty];
                break;
            case 'level':
                DB::table('characters')->where('id', $character->id)->increment('level', $qty);
                $applied[] = ['type'=>'level','amount'=>$qty];
                break;
            case 'skill':
                $skillId = $cfg['skill_id'] ?? ($cfg['code'] ?? null);
                if ($skillId) {
                    $exists = DB::table('character_skills')->where('character_id', $character->id)->where('skill_id', $skillId)->exists();
                    if (!$exists) {
                        DB::table('character_skills')->insert(['character_id'=>$character->id,'skill_id'=>$skillId,'created_at'=>Carbon::now(),'updated_at'=>Carbon::now()]);
                    }
                    $applied[] = ['type'=>'skill','skill_id'=>$skillId];
                }
                break;
            case 'pet':
                $pool = $cfg['pool'] ?? [];
                if (!is_array($pool) || empty($pool)) return;
                $petId = $this->selectPetForCharacter($character->id, $pool);
                if ($petId) {
                    $exists = DB::table('character_pets')->where('character_id',$character->id)->where('pet_id',$petId)->exists();
                    if (!$exists) {
                        DB::table('character_pets')->insert(['character_id'=>$character->id,'pet_id'=>$petId,'level'=>1,'xp'=>0,'created_at'=>Carbon::now(),'updated_at'=>Carbon::now()]);
                    }
                    $applied[] = ['type'=>'pet','pet_id'=>$petId];
                }
                break;
            case 'prestige':
                if (self::schemaHasColumn('characters','prestige')) {
                    DB::table('characters')->where('id', $character->id)->increment('prestige', $qty);
                }
                $applied[] = ['type'=>'prestige','amount'=>$qty];
                break;
            case 'merit':
                Log::warning('redeem exchange: merit not mapped to DB, skipping', ['char'=>$character->id,'qty'=>$qty]);
                $applied[] = ['type'=>'merit','amount'=>$qty];
                break;
            case 'pvp_coin':
                if (self::schemaHasColumn('characters','pvp_points')) {
                    DB::table('characters')->where('id',$character->id)->increment('pvp_points',$qty);
                    $applied[] = ['type'=>'pvp_coin','amount'=>$qty];
                } else {
                    Log::warning('pvp_coin mapping missing, skipping', ['char'=>$character->id]);
                    $applied[] = ['type'=>'pvp_coin','amount'=>$qty];
                }
                break;
            case 'ss':
                if (self::schemaHasColumn('characters','ss')) {
                    DB::table('characters')->where('id',$character->id)->increment('ss',$qty);
                }
                $applied[] = ['type'=>'ss','amount'=>$qty];
                break;
            case 'dragon_ball':
                $key = 'dragon_ball:'.$character->id;
                $row = $this->readCacheRow($key) ?: ['amount'=>0];
                $row['amount'] = ($row['amount'] ?? 0) + $qty;
                $this->writeCacheRow($key, $row, 60*60*24*365);
                $applied[] = ['type'=>'dragon_ball','amount'=>$qty];
                break;
            case 'item':
            default:
                $code = $cfg['code'] ?? null;
                $itemId = $cfg['item_id'] ?? $code;
                if ($itemId) {
                    $existing = DB::table('character_items')->where('character_id',$character->id)->where('item_id',$itemId)->first();
                    if ($existing) {
                        DB::table('character_items')->where('id',$existing->id)->increment('quantity',$qty);
                    } else {
                        DB::table('character_items')->insert(['character_id'=>$character->id,'item_id'=>$itemId,'quantity'=>$qty,'created_at'=>Carbon::now(),'updated_at'=>Carbon::now()]);
                    }
                    $applied[] = ['type'=>'item','item_id'=>$itemId,'quantity'=>$qty];
                } else {
                    Log::warning('redeem exchange: unknown type, skipped', ['cfg'=>$cfg]);
                }
                break;
        }
    }

    protected function selectPetForCharacter(int $charId, array $pool): ?string
    {
        $historyKey = $this->petHistoryPrefix.$charId;
        $history = $this->readCacheRow($historyKey) ?: [];
        $sixDays = 6 * 24 * 3600;
        $now = time();

        $recent = [];
        foreach ($history as $h) {
            if (($now - ($h['ts'] ?? 0)) < $sixDays) $recent[] = $h['pet'];
        }

        $eligible = array_values(array_diff($pool, $recent));
        if (empty($eligible)) {
            $history = [];
            $eligible = $pool;
        }

        $petId = $eligible[array_rand($eligible)];

        $history[] = ['pet'=>$petId, 'ts'=>$now];
        if (count($history) > 100) $history = array_slice($history, -100);
        $this->writeCacheRow($historyKey, $history, 60*60*24*365);

        return $petId;
    }

    protected function readCacheRow(string $key)
    {
        try {
            $row = DB::table('cache')->where('key', $key)->first();
            if (!$row) return null;
            if ((int)$row->expiration !== 0 && (int)$row->expiration < time()) {
                DB::table('cache')->where('key', $key)->delete();
                return null;
            }
            return json_decode($row->value, true);
        } catch (\Throwable $e) {
            Log::error('readCacheRow error: '.$e->getMessage(), ['key'=>$key]);
            return null;
        }
    }

    protected function writeCacheRow(string $key, $value, int $ttl = 0)
    {
        try {
            $expiration = $ttl > 0 ? time()+$ttl : 0;
            DB::table('cache')->updateOrInsert(['key' => $key], ['value' => json_encode($value, JSON_UNESCAPED_SLASHES), 'expiration' => $expiration]);
        } catch (\Throwable $e) {
            Log::error('writeCacheRow error: '.$e->getMessage(), ['key'=>$key]);
        }
    }

    public static function schemaHasColumn(string $table, string $column): bool
    {
        try {
            $db = env('DB_DATABASE');
            $row = DB::table('information_schema.columns')
                ->where('table_schema', $db)
                ->where('table_name', $table)
                ->where('column_name', $column)
                ->first();
            return (bool)$row;
        } catch (\Throwable $e) {
            Log::error('schemaHasColumn error: '.$e->getMessage(), ['table'=>$table,'column'=>$column]);
            return false;
        }
    }
}