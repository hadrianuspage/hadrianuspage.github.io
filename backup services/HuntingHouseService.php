<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\CharacterHuntingHouse;
use App\Models\CharacterItem;
use App\Models\User;
use App\Models\HuntingHouseItem;
use Carbon\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use App\Models\CharacterPet;

class HuntingHouseService
{
    private $badgeId = "material_509";

    private $bossData = [
        "ene_81" => [
            "id"      => ["ene_81"],
            "name"    => "Ginkotsu",
            "msn_bg"  => "mission_21",
            "lvl"     => 10,
            "rank"    => 4,
            "desc"    => "These wolf-like Ginkotsu live in the forest between the Wind Village and the Fire Village. \nThey are the best hunters in the forest. They always attack adventurers and passersby in the forest.",
            "rewards" => ["material_01", "material_02"],
            "gold"    => 4000,
            "xp"      => 1491
        ],
        "ene_82" => [
            "id"      => ["ene_82"],
            "name"    => "Shikigami Yanki",
            "msn_bg"  => "mission_22",
            "lvl"     => 20,
            "rank"    => 4,
            "desc"    => "Summoned by Kojima. Kojima ordered Yanki to protect Kojima's Third Laboratory.\nYanki will not allow anyone to enter the laboratory.",
            "rewards" => ["material_01", "material_02", "material_03"],
            "gold"    => 5000,
            "xp"      => 4078
        ],
        "ene_83" => [
            "id"      => ["ene_83"],
            "name"    => "Gedo Sessho Seki",
            "msn_bg"  => "mission_83",
            "lvl"     => 25,
            "rank"    => 3,
            "desc"    => "Summoned by Kojima, Gedo Sessho Seki is the guardian of his Third Laboratory.",
            "rewards" => ["material_01", "material_02", "material_03"],
            "gold"    => 6000,
            "xp"      => 6745
        ],
        "ene_84" => [
            "id"      => ["ene_84"],
            "name"    => "Tengu",
            "msn_bg"  => "mission_84",
            "lvl"     => 30,
            "rank"    => 3,
            "desc"    => "Kojima used Kinjutsu to turn dead bodies into these zombie Tengu.\nThese Tengu can recall and use all jutsu they learned when they were alive. Only the summoner may control them.",
            "rewards" => ["material_01", "material_02", "material_03", "material_04"],
            "gold"    => 7000,
            "xp"      => 10602
        ],
        "ene_85" => [
            "id"      => ["ene_85"],
            "name"    => "Tengu Shadow",
            "msn_bg"  => "mission_84",
            "lvl"     => 30,
            "rank"    => 3,
            "desc"    => "A darker variant of Tengu, more dangerous and aggressive.",
            "rewards" => ["material_01", "material_02", "material_03", "material_04"],
            "gold"    => 7000,
            "xp"      => 10602
        ],
        "ene_86" => [
            "id"      => ["ene_86"],
            "name"    => "Byakko",
            "msn_bg"  => "mission_86",
            "lvl"     => 40,
            "rank"    => 2,
            "desc"    => "Many years ago, an escaped ninja attempted to use a Kinjutsu to merge his body with the summon monster 'Byakko' to gain immortality. \nHe failed. 'Byakko' devoured him - it is a violent and cruel monster.",
            "rewards" => ["material_01", "material_02", "material_03", "material_04", "material_05"],
            "gold"    => 14000,
            "xp"      => 17834
        ],
        "ene_106" => [
            "id"      => ["ene_106"],
            "name"    => "Ape King",
            "msn_bg"  => "mission_106",
            "lvl"     => 50,
            "rank"    => 2,
            "desc"    => "Living in the Ape Mountain, Ape King is the leader of all apes.",
            "rewards" => ["material_01", "material_02", "material_03", "material_04", "material_05", "material_06"],
            "gold"    => 20000,
            "xp"      => 48750
        ],
        "ene_120" => [
            "id"      => ["ene_120"],
            "name"    => "Battle Turtle",
            "msn_bg"  => "mission_120",
            "lvl"     => 55,
            "rank"    => 2,
            "desc"    => "Originated from the north, the Battle Turtle is known of its age, which is signified by the thorns on its shell.",
            "rewards" => ["material_01", "material_02", "material_03", "material_04", "material_05", "material_06"],
            "gold"    => 25000,
            "xp"      => 58152
        ],
        "ene_155" => [
            "id"      => ["ene_155"],
            "name"    => "Soul General Mutoh",
            "msn_bg"  => "mission_155",
            "lvl"     => 60,
            "rank"    => 1,
            "desc"    => "Once dead, but resurrected with (Kinjutsu: Reverse Soul Resurrection), Soul General is now a rank SS-criminal who escaped to the Samu Village and serve as a secret weapon.",
            "rewards" => ["material_03", "material_04", "material_05", "material_06"],
            "gold"    => 30000,
            "xp"      => 68225
        ]
    ];

    private $zoneBossPool = [
        1 => ['ene_81'],
        2 => ['ene_82', 'ene_83'],
        3 => ['ene_84', 'ene_85'],
        4 => ['ene_86', 'ene_106'],
        5 => ['ene_120', 'ene_155']
    ];

    private $zoneMaterialDrops = [
        1 => ['material_01', 'material_02'],
        2 => ['material_01', 'material_02', 'material_03'],
        3 => ['material_01', 'material_02', 'material_03', 'material_04'],
        4 => ['material_01', 'material_02', 'material_03', 'material_04', 'material_05'],
        5 => ['material_03', 'material_04', 'material_05']
    ];

    private const MATERIAL_DROP_CHANCE = 40;

    public function getData($charId, $sessionKey = null)
    {
        try {
            $today  = Carbon::today()->toDateString();
            $record = CharacterHuntingHouse::firstOrCreate(['character_id' => $charId]);
            $dailyClaimed = ($record->last_daily_claim_date === $today);

            $badgeCount = CharacterItem::where('character_id', $charId)
                ->where('item_id', $this->badgeId)
                ->value('quantity') ?? 0;

            $zones = [
                ['easyBoss' => ["ene_81"], 'hardBoss' => null],
                ['easyBoss' => null, 'hardBoss' => ["ene_82", "ene_83"]],
                ['easyBoss' => ["ene_84", "ene_85"], 'hardBoss' => null],
                ['easyBoss' => null, 'hardBoss' => ["ene_86", "ene_106"]],
                ['easyBoss' => null, 'hardBoss' => ["ene_120", "ene_155"]]
            ];

            $bosses = [];
            foreach ($this->bossData as $id => $data) {
                $bosses[$id] = (object)[
                    'name'        => $data['name'],
                    'description' => $data['desc'],
                    'rewards'     => $data['rewards'],
                    'lvl'         => $data['lvl'],
                    'gold'        => $data['gold'],
                    'xp'          => $data['xp']
                ];
                if (count($data['id']) > 1) {
                    foreach ($data['id'] as $subId) {
                        if ($subId != $id) $bosses[$subId] = $bosses[$id];
                    }
                }
            }

            return (object)[
                'status'      => 1,
                'zones'       => array_map(fn($z) => (object)$z, $zones),
                'bosses'      => (object)$bosses,
                'material'    => $badgeCount,
                'daily_claim' => $dailyClaimed
            ];
        } catch (\Exception $e) {
            Log::error("HuntingHouse.getData error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to get data'];
        }
    }

    public function startHunting($charId, $zoneId, $sessionKey = null)
    {
        try {
            return DB::transaction(function () use ($charId, $zoneId) {
                $cost = ($zoneId >= 3) ? 10 : 5;

                $char = Character::lockForUpdate()->find($charId);
                if (!$char) {
                    return (object)['status' => 0, 'error' => 'Character not found'];
                }

                $badge = CharacterItem::where('character_id', $charId)
                    ->where('item_id', $this->badgeId)
                    ->lockForUpdate()
                    ->first();

                if (!$badge || $badge->quantity < $cost) {
                    return (object)['status' => 2, 'result' => 'You need ' . $cost . ' Kari Badges for this zone!'];
                }

                $badge->quantity -= $cost;
                $badge->save();

                $battleCode = substr(str_shuffle('abcdefghijklmnopqrstuvwxyz0123456789'), 0, 32);
                $hashInput  = (string)$zoneId . (string)$charId . $battleCode;
                $hash       = hash('sha256', $hashInput);

                return (object)[
                    'status' => 1,
                    'code'   => $battleCode,
                    'hash'   => $hash
                ];
            });
        } catch (\Exception $e) {
            Log::error("HuntingHouse.startHunting error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to start hunting'];
        }
    }

    public function dailyClaim($charId, $sessionKey = null)
    {
        try {
            return DB::transaction(function () use ($charId) {
                $today = Carbon::today()->toDateString();
                $char  = Character::lockForUpdate()->find($charId);

                if (!$char) {
                    return (object)['status' => 0, 'error' => 'Character not found'];
                }

                $record = CharacterHuntingHouse::where('character_id', $charId)->lockForUpdate()->first();

                if ($record && $record->last_daily_claim_date === $today) {
                    return (object)['status' => 2, 'result' => 'Already claimed today!'];
                }

                $user   = User::find($char->user_id);
                $amount = ($user && $user->account_type == 1) ? 10 : 5;

                $badge = CharacterItem::firstOrCreate(
                    ['character_id' => $charId, 'item_id' => $this->badgeId],
                    ['quantity' => 0, 'category' => 'material']
                );
                $badge->quantity += $amount;
                $badge->save();

                if (!$record) {
                    $record = CharacterHuntingHouse::create(['character_id' => $charId]);
                }
                $record->last_daily_claim_date = $today;
                $record->save();

                return (object)['status' => 1, 'material' => $badge->quantity];
            });
        } catch (\Exception $e) {
            Log::error("HuntingHouse.dailyClaim error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to claim reward'];
        }
    }

    public function buyMaterial($charId, $sessionKey = null, $amount = 1)
    {
        try {
            $totalCost = 5 * $amount;
            return DB::transaction(function () use ($charId, $amount, $totalCost) {
                $char = Character::lockForUpdate()->find($charId);
                if (!$char) {
                    return (object)['status' => 0, 'error' => 'Character not found'];
                }

                $user = User::lockForUpdate()->find($char->user_id);
                if (!$user || $user->tokens < $totalCost) {
                    return (object)['status' => 2, 'result' => 'Not enough Tokens!'];
                }

                $user->tokens -= $totalCost;
                $user->save();

                $badge = CharacterItem::where('character_id', $charId)
                    ->where('item_id', $this->badgeId)
                    ->lockForUpdate()
                    ->first();

                if ($badge) {
                    $badge->quantity += $amount;
                    $badge->save();
                } else {
                    CharacterItem::create([
                        'character_id' => $charId,
                        'item_id'      => $this->badgeId,
                        'quantity'     => $amount,
                        'category'     => 'material'
                    ]);
                }

                $finalQty = CharacterItem::where('character_id', $charId)
                    ->where('item_id', $this->badgeId)
                    ->value('quantity') ?? 0;

                return (object)['status' => 1, 'material' => $finalQty];
            });
        } catch (\Exception $e) {
            Log::error("HuntingHouse.buyMaterial error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to buy materials'];
        }
    }

    public function finishHunting($charId, $bossNum, $code = null, $hash = null, $sessionKey = null, $battleData = null)
    {
        Log::info("HuntingHouse.finishHunting", [
            'charId'  => $charId,
            'bossNum' => $bossNum,
        ]);

        try {
            return DB::transaction(function () use ($charId, $bossNum) {

                $char = Character::lockForUpdate()->find($charId);
                if (!$char) {
                    Log::error("finishHunting: character {$charId} not found");
                    return (object)[
                        'status'         => 1,
                        'error'          => 0,
                        'result'         => [0, 0, []],
                        'level'          => 1,
                        'xp'             => 0,
                        'level_up'       => false,
                        'account_tokens' => 0,
                    ];
                }

                $zone     = (int) $bossNum;
                $bossKeys = $this->resolveRandomBossKeys($zone);

                Log::info("finishHunting: random bosses picked", [
                    'zone'   => $zone,
                    'bosses' => $bossKeys
                ]);

                $goldReward = 0;
                $xpReward   = 0;

                foreach ($bossKeys as $key) {
                    $data = $this->bossData[$key] ?? null;
                    if ($data) {
                        $goldReward += $data['gold'];
                        $xpReward   += $data['xp'];
                    }
                }

                $earnedItems  = [];
                $materialPool = $this->zoneMaterialDrops[$zone] ?? ['material_01'];

                foreach ($materialPool as $matId) {
                    $roll = mt_rand(1, 100);
                    if ($roll <= self::MATERIAL_DROP_CHANCE) {
                        $this->addItemToInventory($charId, $matId, 1);
                        $earnedItems[] = $matId;
                        Log::info("Material dropped", ['item' => $matId, 'roll' => $roll]);
                    } else {
                        Log::info("Material missed", ['item' => $matId, 'roll' => $roll]);
                    }
                }

                Log::info("finishHunting rewards", [
                    'zone'         => $zone,
                    'gold'         => $goldReward,
                    'xp'           => $xpReward,
                    'bosses'       => $bossKeys,
                    'items_earned' => $earnedItems,
                    'items_missed' => count($materialPool) - count($earnedItems),
                ]);

                $char->gold += $goldReward;

                $levelUp  = false;
                $oldLevel = $char->level;
                $char->xp = ($char->xp ?? 0) + $xpReward;

                $maxLevel = 100;
                $attempts = 0;

                while ($attempts < 20 && $char->level < $maxLevel) {
                    $xpNeeded = $this->xpForLevel($char->level);

                    if ($char->xp >= $xpNeeded) {
                        $char->level++;
                        $char->xp -= $xpNeeded;
                        $levelUp = true;
                        $attempts++;

                        Log::info("Level up!", [
                            'new_level' => $char->level,
                            'xp_used'   => $xpNeeded,
                            'xp_left'   => $char->xp
                        ]);
                    } else {
                        break;
                    }
                }

                $char->save();

                Log::info("finishHunting: char saved", [
                    'old_level' => $oldLevel,
                    'new_level' => $char->level,
                    'gold'      => $char->gold,
                    'xp'        => $char->xp,
                    'levelUp'   => $levelUp,
                    'items'     => $earnedItems,
                ]);

                if (!empty($char->equipped_pet_id)) {
                    try {
                        $pet = CharacterPet::where('character_id', $charId)
                            ->where('id', $char->equipped_pet_id)
                            ->lockForUpdate()
                            ->first();

                        if ($pet) {
                            $petXpGain = (int) floor($xpReward * 0.2);
                            $pet->xp   = ($pet->xp ?? 0) + $petXpGain;

                            $maxPetLevel = min($char->level, 100);
                            $petAttempts = 0;

                            while ($petAttempts < 10 && $pet->level < $maxPetLevel) {
                                $petXpNeeded = $this->petXpForLevel($pet->level);

                                if ($pet->xp >= $petXpNeeded) {
                                    $pet->level++;
                                    $pet->xp -= $petXpNeeded;
                                    $petAttempts++;
                                } else {
                                    break;
                                }
                            }

                            $pet->save();
                        }
                    } catch (\Exception $e) {
                        Log::error("finishHunting pet XP error: " . $e->getMessage());
                    }
                }

                $accountTokens = 0;
                try {
                    $user          = User::find($char->user_id);
                    $accountTokens = $user ? (int)($user->tokens ?? 0) : 0;
                } catch (\Exception $e) {
                    Log::error("finishHunting tokens fetch error: " . $e->getMessage());
                }

                return (object)[
                    'status'         => 1,
                    'error'          => 0,
                    'result'         => [$goldReward, $xpReward, $earnedItems],
                    'level'          => $char->level,
                    'xp'             => $char->xp,
                    'level_up'       => $levelUp,
                    'account_tokens' => $accountTokens,
                ];
            });

        } catch (\Exception $e) {
            Log::error("HuntingHouse.finishHunting EXCEPTION: " . $e->getMessage());
            Log::error("File: " . $e->getFile() . " Line: " . $e->getLine());
            Log::error("Trace: " . $e->getTraceAsString());

            return (object)[
                'status'         => 1,
                'error'          => 0,
                'result'         => [1000, 500, []],
                'level'          => 1,
                'xp'             => 0,
                'level_up'       => false,
                'account_tokens' => 0,
            ];
        }
    }

    public function getItems($charId, $sessionKey = null)
    {
        try {
            $items          = HuntingHouseItem::orderBy('sort_order')->get();
            $formattedItems = [];

            foreach ($items as $item) {
                $formattedItems[] = (object)[
                    'item'         => $item->item_id,
                    'requirements' => (object)[
                        'materials' => $item->materials,
                        'qty'       => $item->quantities
                    ]
                ];
            }

            return (object)['status' => 1, 'items' => $formattedItems];
        } catch (\Exception $e) {
            Log::error("HuntingHouse.getItems error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to get items'];
        }
    }

    public function forgeItem($charId, $sessionKey = null, $targetItemId = null)
    {
        try {
            return DB::transaction(function () use ($charId, $targetItemId) {
                $recipe = HuntingHouseItem::where('item_id', $targetItemId)->first();

                if (!$recipe) {
                    return (object)['status' => 0, 'error' => 'Recipe not found!'];
                }

                $materials  = $recipe->materials;
                $quantities = $recipe->quantities;

                foreach ($materials as $index => $matId) {
                    $qtyNeeded = $quantities[$index];
                    $invItem   = CharacterItem::where('character_id', $charId)
                        ->where('item_id', $matId)
                        ->first();

                    if (!$invItem || $invItem->quantity < $qtyNeeded) {
                        return (object)['status' => 2, 'result' => 'Not enough materials!'];
                    }
                }

                foreach ($materials as $index => $matId) {
                    $qtyNeeded = $quantities[$index];
                    $invItem   = CharacterItem::where('character_id', $charId)
                        ->where('item_id', $matId)
                        ->lockForUpdate()
                        ->first();

                    if ($invItem->quantity == $qtyNeeded) {
                        $invItem->delete();
                    } else {
                        $invItem->quantity -= $qtyNeeded;
                        $invItem->save();
                    }
                }

                $this->addItemToInventory($charId, $targetItemId, 1);

                return (object)[
                    'status'       => 1,
                    'item'         => $targetItemId,
                    'requirements' => [$materials, $quantities]
                ];
            });
        } catch (\Exception $e) {
            Log::error("HuntingHouse.forgeItem error: " . $e->getMessage());
            return (object)['status' => 0, 'error' => 'Failed to forge item'];
        }
    }

    private function resolveRandomBossKeys(int $zone): array
    {
        $pool = $this->zoneBossPool[$zone] ?? ['ene_81'];

        if (count($pool) === 1) {
            return $pool;
        }

        shuffle($pool);

        $min   = 1;
        $max   = count($pool);
        $count = mt_rand($min, $max);

        return array_slice($pool, 0, $count);
    }

    private function xpForLevel(int $level): int
    {
        if ($level <= 1) return 1000;
        return (int) (1000 + ($level * 250));
    }

    private function petXpForLevel(int $level): int
    {
        if ($level <= 1) return 500;
        return (int) (500 + ($level * 150));
    }

    private function addItemToInventory(int $charId, string $itemId, int $quantity = 1): void
    {
        try {
            $category = $this->determineItemCategory($itemId);

            $invItem = CharacterItem::where('character_id', $charId)
                ->where('item_id', $itemId)
                ->first();

            if ($invItem) {
                $invItem->quantity += $quantity;
                $invItem->save();
            } else {
                CharacterItem::create([
                    'character_id' => $charId,
                    'item_id'      => $itemId,
                    'quantity'     => $quantity,
                    'category'     => $category,
                ]);
            }
        } catch (\Exception $e) {
            Log::error("addItemToInventory error [{$itemId}]: " . $e->getMessage());
        }
    }

    private function determineItemCategory(string $itemId): string
    {
        if (str_starts_with($itemId, 'wpn_'))       return 'weapon';
        if (str_starts_with($itemId, 'back_'))      return 'back';
        if (str_starts_with($itemId, 'set_'))       return 'set';
        if (str_starts_with($itemId, 'hair_'))      return 'hair';
        if (str_starts_with($itemId, 'accessory_')) return 'accessory';
        if (str_starts_with($itemId, 'pet_'))       return 'pet';
        if (str_starts_with($itemId, 'material_'))  return 'material';
        if (str_starts_with($itemId, 'skill_'))     return 'skill';

        return 'item';
    }
}