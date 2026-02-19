<?php

namespace App\Services\Amf\MailService;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class ExecuteService
{
    protected string $mailboxConfigKey = 'mailbox';
    protected int $pendingTtl = 300;

    public function executeService($args)
    {
        try {
            $command = null;
            $params = [];

            if (is_array($args) && isset($args[0]) && is_array($args[0]) && isset($args[0][0])) {
                $command = $args[0][0];
                $params = $args[1] ?? [];
            } elseif (is_array($args) && isset($args[0]) && is_string($args[0])) {
                $command = $args[0];
                $params = $args[1] ?? [];
            } elseif (is_string($args)) {
                $command = $args;
                $params = [];
            } else {
                Log::warning('ExecuteService: invalid args shape', ['args' => $args]);
                return ['status' => 0, 'error' => 1, 'result' => 'Invalid request format'];
            }

            switch ($command) {
                case 'getMails':
                    return $this->getMails($params);
                case 'openMail':
                    return $this->openMail($params);
                case 'claim':
                case 'claimReward':
                    return $this->claimReward($params);
                case 'claimAllRewards':
                    return $this->claimAllRewards($params);
                case 'deleteAllMails':
                    return $this->deleteAllMails($params);
                case 'deleteMail':
                    return $this->deleteMail($params);
                default:
                    Log::warning('ExecuteService unknown command', ['command' => $command]);
                    return ['status' => 0, 'error' => 1, 'result' => "Unknown command: {$command}"];
            }
        } catch (\Throwable $e) {
            Log::error('ExecuteService fatal: '.$e->getMessage(), ['exception' => $e]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    protected function loadMailboxConfig(): array
    {
        try {
            $row = DB::table('game_configs')->where('key', $this->mailboxConfigKey)->first();
            if (!$row) return [];
            $value = json_decode($row->value, true);
            return is_array($value) ? $value : [];
        } catch (\Throwable $e) {
            Log::error('loadMailboxConfig error: '.$e->getMessage(), ['exception'=>$e]);
            return [];
        }
    }

    protected function deterministicMailId(string $tplKey, int $charId): int
    {
        $base = (int) substr(sprintf('%u', crc32($tplKey)), -6);
        return $base + ($charId % 1000);
    }

    protected function getPendingKey(int $charId, int $mailId): string
    {
        return "mail_pending:{$charId}:{$mailId}";
    }

    protected function readCache(string $key)
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
            Log::error('readCache error: '.$e->getMessage(), ['key' => $key]);
            return null;
        }
    }

    protected function writeCache(string $key, $value, int $ttl = 0)
    {
        try {
            $expiration = $ttl > 0 ? time() + $ttl : 0;
            $json = json_encode($value, JSON_UNESCAPED_SLASHES);
            DB::table('cache')->updateOrInsert(['key' => $key], ['value' => $json, 'expiration' => $expiration]);
        } catch (\Throwable $e) {
            Log::error('writeCache error: '.$e->getMessage(), ['key' => $key]);
        }
    }

    protected function deleteCache(string $key)
    {
        try {
            DB::table('cache')->where('key', $key)->delete();
        } catch (\Throwable $e) {
            Log::error('deleteCache error: '.$e->getMessage(), ['key' => $key]);
        }
    }

    protected function emptyMails()
    {
        return ['status' => 1, 'mails' => [], 'total' => 0, 'current_page' => 1, 'total_pages' => 0, 'page' => ['current' => 1, 'total' => 0]];
    }

    public function getMails(array $params)
    {
        $charId = isset($params[0]) ? (int)$params[0] : null;
        if (!$charId) return $this->emptyMails();

        $templates = $this->loadMailboxConfig();
        if (empty($templates)) return $this->emptyMails();

        $claimedArr = [];
        try {
            $char = DB::table('characters')->where('id', $charId)->first();
            if ($char && !empty($char->claimed_welcome_rewards)) {
                $decoded = json_decode($char->claimed_welcome_rewards, true);
                $claimedArr = is_array($decoded) ? $decoded : [];
            }
        } catch (\Throwable $e) {
            Log::error('getMails character lookup failed: '.$e->getMessage(), ['charId' => $charId]);
        }

        $mails = [];
        $now = Carbon::now()->format('Y-m-d H:i');

        foreach ($templates as $index => $tpl) {
            $tplKey = $tpl['key'] ?? ($tpl['id'] ?? ('mail_'.$index));
            $mailId = $this->deterministicMailId($tplKey, $charId);

            $rewards = $tpl['rewards'] ?? [];
            $hasRewards = !empty($rewards);

            $mail = [
                'id' => $mailId,
                'mail_id' => $mailId,
                'template_key' => $tplKey,
                'char_id' => $charId,
                'sender_id' => 0,
                'clan_id' => 0,
                'mail_title' => $tpl['title'] ?? 'Mail',
                'mail_sender' => 'System',
                'sent_date' => $now,
                'mail_body' => $tpl['body'] ?? '',
                'mail_viewed' => 0,
                'mail_rewards' => $hasRewards ? $this->serializeRewardsForLabel($rewards) : '',
                'mail_claimed' => ($hasRewards ? 0 : 1),
                'mail_type' => 5,
                'sender_name' => 'System',
                'sender' => 'System',
                'from' => 'System',
                'subject' => $tpl['title'] ?? 'Mail',
                'title' => $tpl['title'] ?? 'Mail',
                'message' => $tpl['body'] ?? '',
                'content' => $tpl['body'] ?? '',
                'body' => $tpl['body'] ?? '',
                'reward_data' => json_encode($rewards, JSON_UNESCAPED_SLASHES),
                'items' => '',
                'is_read' => 0,
                'reward_claimed' => 0,
                'mail_date' => $now,
                'date' => $now,
                'created_at' => $now,
                'time' => $now,
            ];

            $claimedKey = 'mailbox:'.$tplKey;
            if (in_array($claimedKey, $claimedArr)) {
                $mail['mail_claimed'] = 1;
            }

            $mails[] = $mail;
        }

        return ['status' => 1, 'mails' => $mails, 'total' => count($mails), 'current_page' => 1, 'total_pages' => 1, 'page' => ['current' => 1, 'total' => count($mails)]];
    }

    public function openMail(array $params)
    {
        $charId = isset($params[0]) ? (int)$params[0] : null;
        $mailId = isset($params[2]) ? (int)$params[2] : null;
        if (!$charId) return ['status' => 1, 'mail' => new \stdClass()];

        $templates = $this->loadMailboxConfig();
        if (empty($templates)) return ['status' => 1, 'mail' => new \stdClass()];

        $now = Carbon::now()->format('Y-m-d H:i');
        $found = null;
        foreach ($templates as $index => $tpl) {
            $tplKey = $tpl['key'] ?? ($tpl['id'] ?? ('mail_'.$index));
            $expectedId = $this->deterministicMailId($tplKey, $charId);
            if ($expectedId === $mailId) {
                $rewards = $tpl['rewards'] ?? [];
                $hasRewards = !empty($rewards);
                $found = [
                    'id' => $mailId,
                    'mail_id' => $mailId,
                    'template_key' => $tplKey,
                    'char_id' => $charId,
                    'sender_id' => 0,
                    'clan_id' => 0,
                    'mail_title' => $tpl['title'] ?? 'Mail',
                    'mail_sender' => 'System',
                    'sent_date' => $now,
                    'mail_body' => $tpl['body'] ?? '',
                    'mail_viewed' => 1,
                    'mail_rewards' => $hasRewards ? $this->serializeRewardsForLabel($rewards) : '',
                    'mail_claimed' => ($hasRewards ? 0 : 1),
                    'mail_type' => 5,
                    'sender_name' => 'System',
                    'sender' => 'System',
                    'from' => 'System',
                    'subject' => $tpl['title'] ?? 'Mail',
                    'title' => $tpl['title'] ?? 'Mail',
                    'message' => $tpl['body'] ?? '',
                    'content' => $tpl['body'] ?? '',
                    'body' => $tpl['body'] ?? '',
                    'reward_data' => json_encode($rewards, JSON_UNESCAPED_SLASHES),
                    'items' => '',
                    'is_read' => 1,
                    'reward_claimed' => 0,
                    'mail_date' => $now,
                    'date' => $now,
                    'created_at' => $now,
                    'time' => $now,
                ];

                try {
                    $char = DB::table('characters')->where('id', $charId)->first();
                    $claimedArr = [];
                    if ($char && !empty($char->claimed_welcome_rewards)) {
                        $claimedArr = json_decode($char->claimed_welcome_rewards, true) ?: [];
                    }
                    $claimedKey = 'mailbox:'.$tplKey;
                    if (in_array($claimedKey, $claimedArr)) $found['mail_claimed'] = 1;
                } catch (\Throwable $e) {
                    Log::error('openMail claimed lookup failed: '.$e->getMessage(), ['charId'=>$charId]);
                }

                break;
            }
        }

        return ['status' => 1, 'mail' => $found ?? new \stdClass()];
    }

    public function claimReward(array $params)
    {
        Log::info('claimReward called', ['params' => $params]);

        $charId = isset($params[0]) ? (int)$params[0] : null;
        $mailId = isset($params[2]) ? (int)$params[2] : null;
        if (!$charId || !$mailId) {
            Log::warning('claimReward missing params', ['params'=>$params]);
            return ['status' => 0, 'error' => 1, 'result' => 'Invalid params'];
        }

        $templates = $this->loadMailboxConfig();
        $tpl = null;
        foreach ($templates as $index => $t) {
            $tplKey = $t['key'] ?? ($t['id'] ?? ('mail_'.$index));
            $expectedId = $this->deterministicMailId($tplKey, $charId);
            if ($expectedId === $mailId) { $tpl = $t; break; }
        }

        if (!$tpl) {
            Log::warning('claimReward: template not found for mailId', ['charId'=>$charId,'mailId'=>$mailId]);
            return ['status'=>1,'error'=>0,'result'=>'No claimable mails were found.','rewards'=>[]];
        }

        $rewards = $tpl['rewards'] ?? [];
        if (empty($rewards)) {
            try {
                $char = DB::table('characters')->where('id', $charId)->first();
                $claimedArr = [];
                if ($char && !empty($char->claimed_welcome_rewards)) {
                    $claimedArr = json_decode($char->claimed_welcome_rewards, true) ?: [];
                }
                $claimedKey = 'mailbox:'.$tpl['key'];
                if (!in_array($claimedKey, $claimedArr)) {
                    $claimedArr[] = $claimedKey;
                    DB::table('characters')->where('id',$charId)->update(['claimed_welcome_rewards' => json_encode(array_values(array_unique($claimedArr)), JSON_UNESCAPED_SLASHES), 'updated_at'=>Carbon::now()]);
                }
            } catch (\Throwable $e) {
                Log::error('claimReward mark no-reward failed: '.$e->getMessage());
            }
            return ['status'=>1,'error'=>0,'result'=>'No rewards for this mail','rewards'=>[]];
        }

        $claimedArr = [];
        try {
            $char = DB::table('characters')->where('id', $charId)->first();
            if ($char && !empty($char->claimed_welcome_rewards)) {
                $claimedArr = json_decode($char->claimed_welcome_rewards, true) ?: [];
            }
        } catch (\Throwable $e) {
            Log::error('claimReward character lookup failed: '.$e->getMessage());
        }
        $claimedKey = 'mailbox:'.$tpl['key'];
        if (in_array($claimedKey, $claimedArr)) {
            Log::info('claimReward already claimed', ['charId'=>$charId,'mailId'=>$mailId]);
            return ['status'=>1,'error'=>0,'result'=>'No claimable mails were found.','rewards'=>[]];
        }

        $pendingKey = $this->getPendingKey($charId, $mailId);
        $pending = $this->readCache($pendingKey);

        if (!$pending) {
            $preview = $this->buildRichPreview($rewards);
            $this->writeCache($pendingKey, ['rewards'=>$rewards,'created_at'=>time()], $this->pendingTtl);
            Log::info('claimReward preview created', ['charId'=>$charId,'mailId'=>$mailId,'preview_count'=>count($preview)]);
            return ['status'=>1,'error'=>0,'result'=>'Reward preview','rewards'=>$preview];
        }

        $storedRewards = $pending['rewards'] ?? $rewards;
        $applied = [];
        try {
            $character = DB::table('characters')->where('id', $charId)->first();
            $user = $character ? DB::table('users')->where('id', $character->user_id)->first() : null;
        } catch (\Throwable $e) {
            Log::error('claimReward user lookup failed: '.$e->getMessage());
            return ['status'=>0,'error'=>1,'result'=>'Internal server error'];
        }

        DB::beginTransaction();
        try {
            foreach ($storedRewards as $r) {
                try {
                    $this->applyReward($character, $user, $r, $applied);
                } catch (\Throwable $inner) {
                    Log::error('claimReward apply error: '.$inner->getMessage(), ['reward'=>$r]);
                }
            }

            $claimedArr[] = $claimedKey;
            $claimedArr = array_values(array_unique($claimedArr));
            DB::table('characters')->where('id',$charId)->update(['claimed_welcome_rewards'=>json_encode($claimedArr, JSON_UNESCAPED_SLASHES),'updated_at'=>Carbon::now()]);

            $this->deleteCache($pendingKey);
            DB::commit();

            Log::info('claimReward success', ['charId'=>$charId,'mailId'=>$mailId,'applied'=>$applied]);
            $final = $this->buildRichPreviewFromApplied($applied);
            return ['status'=>1,'error'=>0,'result'=>'Reward claimed','rewards'=>$final];
        } catch (\Throwable $e) {
            DB::rollBack();
            Log::error('claimReward fatal: '.$e->getMessage(), ['exception'=>$e]);
            return ['status'=>0,'error'=>1,'result'=>'Claim failed: internal error'];
        }
    }

    protected function buildRichPreview(array $rewards): array
    {
        $preview = [];
        foreach ($rewards as $r) {
            $type = $r['type'] ?? null;
            if (!$type) continue;
            switch ($type) {
                case 'tokens':
                    $amt = (int)($r['amount'] ?? 0);
                    $preview[] = ['type'=>'tokens','id'=>'tokens','amount'=>$amt,'quantity'=>$amt,'display'=>"x{$amt}",'title'=>'Tokens'];
                    break;
                case 'skill':
                    $sid = $r['skill_id'] ?? '';
                    $preview[] = ['type'=>'skill','id'=>$sid,'skill_id'=>$sid,'amount'=>1,'quantity'=>1,'display'=>"x1",'title'=>'Skill','name'=>$sid];
                    break;
                case 'pet':
                    $pid = $r['pet_id'] ?? ($r['id'] ?? '');
                    $preview[] = ['type'=>'pet','id'=>$pid,'pet_id'=>$pid,'quantity'=>1,'amount'=>1,'display'=>'x1','title'=>$pid,'name'=>$pid];
                    break;
                case 'level':
                    $up = (int)($r['amount'] ?? 0);
                    $preview[] = ['type'=>'level','id'=>'level','amount'=>$up,'quantity'=>$up,'display'=>"+{$up}",'title'=>'Level'];
                    break;
                case 'gold':
                    $g = (int)($r['amount'] ?? 0);
                    $preview[] = ['type'=>'gold','id'=>'gold','amount'=>$g,'quantity'=>$g,'display'=>"x{$g}",'title'=>'Gold'];
                    break;
                case 'tp':
                    $t = (int)($r['amount'] ?? 0);
                    $preview[] = ['type'=>'tp','id'=>'tp','amount'=>$t,'quantity'=>$t,'display'=>"x{$t}",'title'=>'TP'];
                    break;
                default:
                    $preview[] = ['type'=>'unknown','id'=>'','amount'=>0,'quantity'=>0,'display'=>''];
                    break;
            }
        }
        return $preview;
    }

    protected function buildRichPreviewFromApplied(array $applied): array
    {
        $out = [];
        foreach ($applied as $a) {
            $type = $a['type'] ?? null;
            if (!$type) continue;
            switch ($type) {
                case 'tokens':
                    $amt = (int)($a['amount'] ?? 0);
                    $out[] = ['type'=>'tokens','id'=>'tokens','amount'=>$amt,'quantity'=>$amt,'display'=>"x{$amt}",'title'=>'Tokens'];
                    break;
                case 'skill':
                    $sid = $a['skill_id'] ?? '';
                    $out[] = ['type'=>'skill','id'=>$sid,'skill_id'=>$sid,'amount'=>1,'quantity'=>1,'display'=>'x1','title'=>'Skill'];
                    break;
                case 'pet':
                    $pid = $a['pet_id'] ?? ($a['id'] ?? '');
                    $out[] = ['type'=>'pet','id'=>$pid,'pet_id'=>$pid,'amount'=>1,'quantity'=>1,'display'=>'x1','title'=>$pid];
                    break;
                case 'level':
                    $up = (int)($a['amount'] ?? 0);
                    $out[] = ['type'=>'level','id'=>'level','amount'=>$up,'quantity'=>$up,'display'=>"+{$up}",'title'=>'Level'];
                    break;
                case 'gold':
                    $g = (int)($a['amount'] ?? 0);
                    $out[] = ['type'=>'gold','id'=>'gold','amount'=>$g,'quantity'=>$g,'display'=>"x{$g}",'title'=>'Gold'];
                    break;
                case 'tp':
                    $t = (int)($a['amount'] ?? 0);
                    $out[] = ['type'=>'tp','id'=>'tp','amount'=>$t,'quantity'=>$t,'display'=>"x{$t}",'title'=>'TP'];
                    break;
                default:
                    $out[] = $a;
                    break;
            }
        }
        return $out;
    }

    protected function applyReward($character, $user, array $r, array &$applied)
    {
        $charId = $character->id;
        $userId = $character->user_id;
        $type = $r['type'] ?? null;
        if (!$type) return;

        switch ($type) {
            case 'tokens':
                $amount = (int)($r['amount'] ?? 0);
                if ($amount > 0 && $user) {
                    DB::table('users')->where('id',$userId)->increment('tokens',$amount);
                    $applied[] = ['type'=>'tokens','amount'=>$amount];
                }
                break;
            case 'skill':
                $skillId = $r['skill_id'] ?? null;
                if ($skillId) {
                    $exists = DB::table('character_skills')->where('character_id',$charId)->where('skill_id',$skillId)->exists();
                    if (!$exists) DB::table('character_skills')->insert(['character_id'=>$charId,'skill_id'=>$skillId,'created_at'=>Carbon::now(),'updated_at'=>Carbon::now()]);
                    $applied[] = ['type'=>'skill','skill_id'=>$skillId];
                }
                break;
            case 'pet':
                $petId = $r['pet_id'] ?? ($r['id'] ?? null);
                if ($petId) {
                    $exists = DB::table('character_pets')->where('character_id',$charId)->where('pet_id',$petId)->exists();
                    if (!$exists) DB::table('character_pets')->insert(['character_id'=>$charId,'pet_id'=>$petId,'level'=>1,'xp'=>0,'created_at'=>Carbon::now(),'updated_at'=>Carbon::now()]);
                    $applied[] = ['type'=>'pet','pet_id'=>$petId];
                }
                break;
            case 'level':
                $up = (int)($r['amount'] ?? 0);
                if ($up !== 0) { DB::table('characters')->where('id',$charId)->increment('level',$up); $applied[]=['type'=>'level','amount'=>$up]; }
                break;
            case 'gold':
                $g = (int)($r['amount'] ?? 0);
                if ($g !== 0) { DB::table('characters')->where('id',$charId)->increment('gold',$g); $applied[]=['type'=>'gold','amount'=>$g]; }
                break;
            case 'tp':
                $tp = (int)($r['amount'] ?? 0);
                if ($tp !== 0) { DB::table('characters')->where('id',$charId)->increment('tp',$tp); $applied[]=['type'=>'tp','amount'=>$tp]; }
                break;
            default:
                Log::warning('applyReward unknown type', ['reward'=>$r]);
                break;
        }
    }

    public function claimAllRewards(array $params)
    {
        $charId = isset($params[0]) ? (int)$params[0] : null;
        if (!$charId) return ['status'=>0,'error'=>1,'result'=>'Invalid params'];

        $templates = $this->loadMailboxConfig();
        $appliedAll = [];
        foreach ($templates as $t) {
            $mailId = $this->deterministicMailId($t['key'] ?? ($t['id'] ?? '0'), $charId);
            $this->writeCache($this->getPendingKey($charId,$mailId), ['rewards'=>$t['rewards'] ?? [], 'created_at'=>time()], 60);
            $res = $this->claimReward([$charId, null, $mailId]);
            if (!empty($res['rewards'])) $appliedAll = array_merge($appliedAll, $res['rewards']);
        }
        return ['status'=>1,'error'=>0,'result'=>'All claimed','rewards'=>$appliedAll];
    }

    public function deleteAllMails(array $params){ return ['status'=>1,'error'=>0,'result'=>'All Mails have been deleted']; }
    public function deleteMail(array $params){ return ['status'=>1]; }

    protected function serializeRewardsForLabel(array $rewards): string
    {
        $parts = [];
        foreach ($rewards as $r) {
            if (($r['type'] ?? '') === 'tokens') $parts[] = 'tokens_Tokens:'.($r['amount'] ?? 0);
            elseif (($r['type'] ?? '') === 'skill') $parts[] = ($r['skill_id'] ?? '');
            elseif (($r['type'] ?? '') === 'pet') $parts[] = ($r['pet_id'] ?? '');
            elseif (($r['type'] ?? '') === 'gold') $parts[] = 'gold:'.($r['amount'] ?? 0);
            elseif (($r['type'] ?? '') === 'tp') $parts[] = 'tp:'.($r['amount'] ?? 0);
            elseif (($r['type'] ?? '') === 'level') $parts[] = 'level:'.($r['amount'] ?? 0);
        }
        return implode(',', $parts);
    }
}
