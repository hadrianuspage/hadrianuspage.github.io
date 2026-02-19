<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\CharacterThanksgivingEvent;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class ThanksGivingEvent2025Service
{
    private const REFILL_PRICE = 50;
    private const MAX_ENERGY = 10;
    private const ENERGY_REFILL_MINUTES = 20; // 20 menit per energy
    
    /**
     * Static event data - FIXED VALUES
     */
    private $eventData = [
        'bosses' => [
            [
                'id' => ['ene_2113'],
                'name' => 'Cornfield Bandit',
                'description' => 'Cornfield Bandit is a bandit that lives in the cornfields.',
                'levels' => [0, 5],
                'gold' => 2500,    // FIXED: Direct integer
                'xp' => 2500,      // FIXED: Direct integer
                'rewards' => ['material_2221', 'material_2222'],
                'background' => 'mission_1063'
            ],
            [
                'id' => ['ene_2114'],
                'name' => 'Cranberry Mage',
                'description' => 'Cranberry Mage is a mage that lives in the cranberry fields.',
                'levels' => [0, 5],
                'gold' => 3000,
                'xp' => 3000,
                'rewards' => ['material_2221', 'material_2223'],
                'background' => 'mission_1064'
            ],
            [
                'id' => ['ene_2115'],
                'name' => 'Grateful Farmer',
                'description' => 'Grateful Farmer is a farmer that is grateful for the food he grows.',
                'levels' => [0, 5],
                'gold' => 3500,
                'xp' => 3500,
                'rewards' => ['material_2221', 'material_2224'],
                'background' => 'mission_1063'
            ],
            [
                'id' => ['ene_2116'],
                'name' => 'Turkey Champ',
                'description' => 'Turkey Champ is a champion that uses turkeys to attack.',
                'levels' => [0, 5],
                'gold' => 4000,
                'xp' => 4000,
                'rewards' => ['material_2221', 'material_2225'],
                'background' => 'mission_1064'
            ]
        ],
        'package' => [
            'name' => 'Thanksgiving Package',
            'price' => [6499, 4999],
            'rewards' => ['hair_2360_%s', 'set_2400_%s', 'back_2395', 'wpn_2398', 'skill_2322']
        ],
        'milestone_battle' => [
            ['id' => 'gold_100000', 'requirement' => 10, 'quantity' => 1],
            ['id' => 'material_2221', 'requirement' => 50, 'quantity' => 10],
            ['id' => 'hair_2355_%s', 'requirement' => 100, 'quantity' => 1],
            ['id' => 'essential_05', 'requirement' => 200, 'quantity' => 5],
            ['id' => 'set_2395_%s', 'requirement' => 300, 'quantity' => 1],
            ['id' => 'tokens_150', 'requirement' => 400, 'quantity' => 1],
            ['id' => 'back_2389', 'requirement' => 600, 'quantity' => 1],
            ['id' => 'wpn_2392', 'requirement' => 750, 'quantity' => 1]
        ]
    ];

    public function getBattleData($characterId, $sessionkey)
    {
        try {
            Log::info("ThanksGiving getBattleData: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Get or create event record
            $eventRecord = CharacterThanksgivingEvent::firstOrCreate(
                ['character_id' => $characterId],
                [
                    'energy' => self::MAX_ENERGY,
                    'battles_count' => 0,
                    'last_energy_reset' => Carbon::now(),
                    'claimed_milestone_rewards' => json_encode(array_fill(0, 8, false)),
                    'package_bought' => false
                ]
            );

            // Auto refill energy berdasarkan waktu
            $eventRecord->autoRefillEnergy();

            Log::info("ThanksGiving Data: Energy {$eventRecord->energy}, Battles {$eventRecord->battles_count}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => $eventRecord->energy,
                'battles_count' => $eventRecord->battles_count,
                'last_battle_date' => $eventRecord->last_battle_date ? $eventRecord->last_battle_date->format('Y-m-d') : null,
                'next_energy_time' => $eventRecord->getNextEnergyTime()
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving getBattleData Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to get battle data'];
        }
    }

    public function refillEnergy($characterId, $sessionkey)
    {
        try {
            Log::info("ThanksGiving refillEnergy: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $user = $character->user;
            if ($user->tokens < self::REFILL_PRICE) {
                return ['status' => 0, 'error' => 'Insufficient tokens'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                return ['status' => 0, 'error' => 'Event record not found'];
            }

            // Deduct tokens
            $user->tokens -= self::REFILL_PRICE;
            $user->save();

            // Refill energy (full 10 energy dengan token)
            $eventRecord->refillEnergyWithToken();

            Log::info("ThanksGiving Energy Refilled with Token: New energy {$eventRecord->energy}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => $eventRecord->energy
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving refillEnergy Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to refill energy'];
        }
    }

    public function startBattle($characterId, $bossId, $agility, $enemyData, $hash, $sessionkey)
    {
        try {
            Log::info("ThanksGiving startBattle: Char $characterId Boss $bossId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                return ['status' => 0, 'error' => 'Event record not found'];
            }

            // Auto refill energy berdasarkan waktu
            $eventRecord->autoRefillEnergy();

            // Check energy - TIDAK mengurangi energy di sini
            if ($eventRecord->energy <= 0) {
                return ['status' => 0, 'error' => 'Insufficient energy'];
            }

            // Generate battle code
            $battleCode = 'TG' . time() . rand(1000, 9999);

            // Generate response hash
            $responseHash = hash('sha256', $bossId . $battleCode . $characterId);

            Log::info("ThanksGiving Battle Started: Code $battleCode, Current Energy: {$eventRecord->energy}");

            return [
                'status' => 1,
                'error' => 0,
                'code' => $battleCode,
                'hash' => $responseHash
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving startBattle Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to start battle'];
        }
    }

    public function finishBattle($characterId, $bossId, $won, $sessionkey)
    {
        try {
            // FIXED: Force win for testing - ignore client won parameter
            $wonBool = true;
            
            Log::info("ThanksGiving finishBattle: Char $characterId Boss $bossId Won " . ($wonBool ? 'Yes' : 'No'));

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                return ['status' => 0, 'error' => 'Event record not found'];
            }

            // Auto refill energy berdasarkan waktu
            $eventRecord->autoRefillEnergy();

            // KURANGI ENERGY DI SINI (setelah battle selesai)
            if ($eventRecord->energy <= 0) {
                return ['status' => 0, 'error' => 'No energy available'];
            }

            // Deduct energy setelah battle selesai
            $eventRecord->useEnergy(1);

            // Find boss data
            $bossData = $this->getBossData($bossId);
            if (!$bossData) {
                Log::error("ThanksGiving: Boss not found - $bossId");
                return ['status' => 0, 'error' => 'Boss not found'];
            }

            Log::info("ThanksGiving: Found boss data - Gold: {$bossData['gold']}, XP: {$bossData['xp']}");

            $goldEarned = 0;
            $xpEarned   = 0;
            $materials  = [];
            $levelUp    = false;

            if ($wonBool) {
                $goldEarned = (int)$bossData['gold'];
                $xpEarned   = (int)$bossData['xp'];

                // Increment battle count
                $eventRecord->incrementBattles();

                // Add gold and XP
                $character->gold += $goldEarned;
                $levelUp = $character->addXp($xpEarned);
                $character->save();

                // Generate material rewards
                if (!empty($bossData['rewards'])) {
                    $randomMaterial = $bossData['rewards'][array_rand($bossData['rewards'])];
                    $quantity       = rand(1, 3);

                    $item = CharacterItem::firstOrCreate(
                        [
                            'character_id' => $character->id,
                            'item_id'      => $randomMaterial,
                            'category'     => 'material'
                        ],
                        ['quantity' => 0]
                    );
                    $item->quantity += $quantity;
                    $item->save();

                    $materials[] = $randomMaterial;
                    Log::info("ThanksGiving Reward: $randomMaterial x$quantity");
                }

                Log::info("ThanksGiving Battle Won: Battles now {$eventRecord->battles_count}, Gold +$goldEarned, XP +$xpEarned, Energy: {$eventRecord->energy}");
            } else {
                Log::info("ThanksGiving Battle Lost: No rewards, Energy: {$eventRecord->energy}");
            }

            // FORMAT SAMA PERSIS SEPERTI FinishService.php
            return [
                'status'       => 1,
                'error'        => 0,
                'result'       => [
                    (int)$xpEarned,
                    (int)$goldEarned,
                    $materials   // Item/material rewards array
                ],
                'level'        => (int)$character->level,
                'xp'           => (int)$character->xp,
                'level_up'     => $levelUp,
                'battles_count'=> (int)$eventRecord->battles_count,
                'energy'       => (int)$eventRecord->energy,
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving finishBattle Error: " . $e->getMessage());
            Log::error("ThanksGiving finishBattle Stack: " . $e->getTraceAsString());
            return ['status' => 0, 'error' => 'Failed to finish battle: ' . $e->getMessage()];
        }
    }

    private function getBossData($bossId)
    {
        Log::info("ThanksGiving getBossData: Looking for $bossId");
        
        foreach ($this->eventData['bosses'] as $boss) {
            Log::info("ThanksGiving: Checking boss " . implode(',', $boss['id']));
            if (in_array($bossId, $boss['id'])) {
                Log::info("ThanksGiving: Found boss $bossId with gold: {$boss['gold']}, xp: {$boss['xp']}");
                return $boss;
            }
        }
        
        Log::error("ThanksGiving: Boss $bossId not found in boss data");
        return null;
    }

    public function getBonusRewards($characterId, $sessionkey)
    {
        try {
            Log::info("ThanksGiving getBonusRewards: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                $eventRecord = CharacterThanksgivingEvent::create([
                    'character_id' => $characterId,
                    'energy' => self::MAX_ENERGY,
                    'battles_count' => 0,
                    'claimed_milestone_rewards' => json_encode(array_fill(0, 8, false)),
                    'last_energy_reset' => Carbon::now()
                ]);
            }

            $claimedRewards = $eventRecord->getClaimedRewardsArray();

            return [
                'status' => 1,
                'error' => 0,
                'milestone' => $eventRecord->battles_count,
                'rewards' => $claimedRewards
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving getBonusRewards Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to get bonus rewards'];
        }
    }

    public function claimBonusRewards($characterId, $sessionkey, $rewardIndex)
    {
        try {
            Log::info("ThanksGiving claimBonusRewards: Char $characterId Index $rewardIndex");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                return ['status' => 0, 'error' => 'Event record not found'];
            }

            // Validate index
            if ($rewardIndex < 0 || $rewardIndex >= 8) {
                return ['status' => 0, 'error' => 'Invalid reward index'];
            }

            $milestone = $this->eventData['milestone_battle'][$rewardIndex];

            // Check battles requirement
            if ($eventRecord->battles_count < $milestone['requirement']) {
                return ['status' => 0, 'error' => 'Insufficient battles'];
            }

            // Check if already claimed
            $claimedRewards = $eventRecord->getClaimedRewardsArray();
            
            if ($claimedRewards[$rewardIndex]) {
                return ['status' => 0, 'error' => 'Reward already claimed'];
            }

            // Mark as claimed
            $claimedRewards[$rewardIndex] = true;
            $eventRecord->setClaimedRewardsArray($claimedRewards);
            $eventRecord->save();

            // Process reward
            $rewardId = str_replace('%s', $character->gender, $milestone['id']);
            $quantity = $milestone['quantity'];

            // Add reward
            $this->addRewardToCharacter($character, $rewardId, $quantity);

            Log::info("ThanksGiving Milestone Claimed: Index $rewardIndex Reward $rewardId");

            return [
                'status' => 1,
                'error' => 0,
                'reward' => [$rewardId]
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving claimBonusRewards Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to claim reward'];
        }
    }

    private function addRewardToCharacter($character, $rewardId, $quantity)
    {
        // Handle special rewards
        if (strpos($rewardId, 'gold_') === 0) {
            $amount = (int)str_replace('gold_', '', $rewardId);
            $character->gold += $amount;
            $character->save();
            return;
        }

        if (strpos($rewardId, 'tokens_') === 0) {
            $amount = (int)str_replace('tokens_', '', $rewardId);
            $character->user->tokens += $amount;
            $character->user->save();
            return;
        }

        // Handle skills
        if (strpos($rewardId, 'skill_') === 0) {
            CharacterSkill::firstOrCreate([
                'character_id' => $character->id,
                'skill_id' => $rewardId
            ]);
            return;
        }

        // Handle items
        $category = $this->getCategoryFromItemId($rewardId);
        
        $item = CharacterItem::firstOrCreate(
            [
                'character_id' => $character->id,
                'item_id' => $rewardId,
                'category' => $category
            ],
            ['quantity' => 0]
        );

        $item->quantity += $quantity;
        $item->save();
    }

    private function getCategoryFromItemId($itemId)
    {
        if (strpos($itemId, 'wpn_') === 0) return 'weapon';
        if (strpos($itemId, 'back_') === 0) return 'back';
        if (strpos($itemId, 'set_') === 0) return 'set';
        if (strpos($itemId, 'accessory_') === 0) return 'accessory';
        if (strpos($itemId, 'hair_') === 0) return 'hair';
        if (strpos($itemId, 'material_') === 0) return 'material';
        if (strpos($itemId, 'essential_') === 0) return 'item';
        
        return 'item';
    }

    public function getPackage($characterId, $sessionkey)
    {
        try {
            Log::info("ThanksGiving getPackage: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            
            $bought = $eventRecord ? $eventRecord->package_bought : false;

            return [
                'status' => 1,
                'error' => 0,
                'bought' => $bought
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving getPackage Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to get package'];
        }
    }

    public function buyPackage($characterId, $sessionkey)
    {
        try {
            Log::info("ThanksGiving buyPackage: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $eventRecord = CharacterThanksgivingEvent::where('character_id', $characterId)->first();
            if (!$eventRecord) {
                $eventRecord = CharacterThanksgivingEvent::create([
                    'character_id' => $characterId,
                    'energy' => self::MAX_ENERGY,
                    'battles_count' => 0,
                    'package_bought' => false,
                    'last_energy_reset' => Carbon::now()
                ]);
            }

            // Check if already bought
            if ($eventRecord->package_bought) {
                return ['status' => 0, 'error' => 'Package already purchased'];
            }

            $user = $character->user;
            
            // Check if user has account_type field, fallback to 0
            $accountType = isset($user->account_type) && $user->account_type > 0 ? 1 : 0;
            $price = $this->eventData['package']['price'][$accountType];

            // Check tokens
            if ($user->tokens < $price) {
                return ['status' => 0, 'error' => 'Insufficient tokens'];
            }

            // Deduct tokens
            $user->tokens -= $price;
            $user->save();

            // Mark as bought
            $eventRecord->package_bought = true;
            $eventRecord->save();

            // Give package rewards
            foreach ($this->eventData['package']['rewards'] as $rewardId) {
                $processedId = str_replace('%s', $character->gender, $rewardId);
                $this->addRewardToCharacter($character, $processedId, 1);
            }

            Log::info("ThanksGiving Package Bought: Price $price");

            return [
                'status' => 1,
                'error' => 0
            ];

        } catch (\Exception $e) {
            Log::error("ThanksGiving buyPackage Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to buy package'];
        }
    }
}