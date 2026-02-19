<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use App\Models\CharacterConfrontingDeath;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class ConfrontingDeathEvent2025Service
{
    private const REFILL_PRICE = 50;
    private const MAX_ENERGY = 8;

    /**
     * Static event data - FIXED VALUES
     */
    private $eventData = [
        'bosses' => [
            'id' => [
                'battle_1' => ['ene_2107', 'ene_2108', 'ene_2109'],
                'battle_2' => ['ene_2112', 'ene_2110', 'ene_2111']
            ],
            'name' => 'Lord of the Underworld - Hades',
            'description' => 'Lord of the Underworld is the ruler of the underworld. He is the one who controls the dead and the living. He is the one who controls the fate of the world.',
            'levels' => [0, 5],
            'gold_formula' => 'level * 2500 / 60',
            'xp_formula' => 'level * 2500 / 60',
            'rewards' => ['material_2216', 'material_2217', 'material_2218', 'material_2219', 'material_2220'],
            'background' => ['mission_1061', 'mission_1062']
        ],
        'training' => [
            [
                'id' => 'skill_2313',
                'price' => [3999, 2999],
                'name' => 'Erebos Beam'
            ],
            [
                'id' => 'skill_2314',
                'price' => [1999, 1999],
                'name' => 'Advance Erebos Beam'
            ]
        ],
        'rewards_preview' => [
            'hair' => ['hair_2351_%s', 'hair_2352_%s'],
            'set' => ['set_2391_%s', 'set_2392_%s'],
            'back' => ['back_2384', 'back_2385', 'back_2386'],
            'weapon' => ['wpn_2387', 'wpn_2388', 'wpn_2389'],
            'skill' => ['skill_2311', 'skill_2312']
        ],
        'milestone_battle' => [
            ['id' => 'gold_100000', 'requirement' => 10, 'quantity' => 1],
            ['id' => 'material_2219', 'requirement' => 50, 'quantity' => 10],
            ['id' => 'hair_2350_%s', 'requirement' => 100, 'quantity' => 1],
            ['id' => 'essential_05', 'requirement' => 200, 'quantity' => 5],
            ['id' => 'set_2390_%s', 'requirement' => 300, 'quantity' => 1],
            ['id' => 'tokens_150', 'requirement' => 400, 'quantity' => 1],
            ['id' => 'back_2383', 'requirement' => 600, 'quantity' => 1],
            ['id' => 'wpn_2386', 'requirement' => 750, 'quantity' => 1]
        ]
    ];

    /**
     * Get battle data (energy, battles, milestone)
     */
    public function getBattleData($characterId, $sessionkey)
    {
        try {
            Log::info("ConfrontingDeath getBattleData: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Auto refill energy berdasarkan waktu
            $data = CharacterConfrontingDeath::autoRefillEnergy($characterId);

            Log::info("ConfrontingDeath Data: Energy {$data['energy']}, Battles {$data['total_battles']}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => (int)$data['energy'],
                'total_battles' => (int)$data['total_battles'],
                'milestone_data' => $data['milestone_data'],
                'next_energy_time' => CharacterConfrontingDeath::getNextEnergyTime($characterId)
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath getBattleData Error: " . $e->getMessage());
            Log::error("Stack trace: " . $e->getTraceAsString());
            return ['status' => 0, 'error' => 'Failed to get battle data: ' . $e->getMessage()];
        }
    }

    /**
     * Refill energy dengan token (50 tokens = full energy)
     */
    public function refillEnergy($characterId, $sessionkey)
    {
        try {
            Log::info("ConfrontingDeath refillEnergy: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $user = $character->user;
            if ($user->tokens < self::REFILL_PRICE) {
                return ['status' => 0, 'error' => 'Insufficient tokens'];
            }

            // Deduct tokens
            $user->tokens -= self::REFILL_PRICE;
            $user->save();

            // Refill energy
            $data = CharacterConfrontingDeath::refillEnergyWithToken($characterId);

            Log::info("ConfrontingDeath Energy Refilled: New energy {$data['energy']}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => (int)$data['energy']
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath refillEnergy Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to refill energy'];
        }
    }

    /**
     * Start battle (generate battle code)
     */
    public function startBattle($characterId, $bossId, $agility, $enemyData, $hash, $sessionkey)
    {
        try {
            Log::info("ConfrontingDeath startBattle: Char $characterId Boss $bossId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Auto refill energy berdasarkan waktu
            $data = CharacterConfrontingDeath::autoRefillEnergy($characterId);

            // Check energy - TIDAK mengurangi energy di sini
            if ($data['energy'] <= 0) {
                return ['status' => 0, 'error' => 'Insufficient energy'];
            }

            // Generate battle code
            $battleCode = 'CD' . time() . rand(1000, 9999);

            // Generate response hash
            $responseHash = hash('sha256', $bossId . $battleCode . $characterId);

            Log::info("ConfrontingDeath Battle Started: Code $battleCode, Current Energy: {$data['energy']}");

            return [
                'status' => 1,
                'error' => 0,
                'code' => $battleCode,
                'hash' => $responseHash
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath startBattle Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to start battle'];
        }
    }

    /**
     * Finish battle (reward calculation)
     */
    public function finishBattle($characterId, $bossId, $won, $sessionkey)
    {
        try {
            // Force win for testing
            $wonBool = true;
            
            Log::info("ConfrontingDeath finishBattle START: Char $characterId Boss $bossId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Get current data BEFORE any changes
            $beforeData = CharacterConfrontingDeath::getData($characterId);
            Log::info("ConfrontingDeath BEFORE battle: Energy {$beforeData['energy']}, Battles {$beforeData['total_battles']}");

            // Auto refill energy berdasarkan waktu
            $data = CharacterConfrontingDeath::autoRefillEnergy($characterId);

            // Check energy availability
            if ($data['energy'] <= 0) {
                Log::warning("ConfrontingDeath finishBattle: No energy available");
                return ['status' => 0, 'error' => 'No energy available'];
            }

            // KURANGI ENERGY DI SINI (setelah battle selesai)
            $energyUsed = CharacterConfrontingDeath::useEnergy($characterId, 1);
            
            if (!$energyUsed) {
                Log::error("ConfrontingDeath finishBattle: Failed to use energy");
                return ['status' => 0, 'error' => 'Failed to use energy'];
            }

            // Calculate rewards using formula
            $bossData = $this->eventData['bosses'];
            $level = $character->level;
            
            // Calculate gold: level * 2500 / 60
            $goldCalculated = (int)($level * 2500 / 60);
            
            // Calculate XP: level * 2500 / 60
            $xpCalculated = (int)($level * 2500 / 60);
            
            Log::info("ConfrontingDeath: Boss data - Gold: $goldCalculated, XP: $xpCalculated (Level: $level)");

            $goldEarned = 0;
            $xpEarned   = 0;
            $materials  = [];
            $levelUp    = false;

            if ($wonBool) {
                $goldEarned = $goldCalculated;
                $xpEarned   = $xpCalculated;

                // Increment battle count - PENTING!
                CharacterConfrontingDeath::incrementBattles($characterId);

                // Add gold and XP
                $character->gold += $goldEarned;
                $levelUp = $character->addXp($xpEarned);
                $character->save();

                // Generate material rewards (30% chance each)
                if (!empty($bossData['rewards'])) {
                    foreach ($bossData['rewards'] as $material) {
                        if (rand(1, 100) <= 30) { // 30% chance
                            $quantity = rand(1, 2);

                            $item = CharacterItem::firstOrCreate(
                                [
                                    'character_id' => $character->id,
                                    'item_id'      => $material,
                                    'category'     => $this->getCategoryFromItemId($material)
                                ],
                                ['quantity' => 0]
                            );
                            $item->quantity += $quantity;
                            $item->save();

                            $materials[] = $material;
                            Log::info("ConfrontingDeath Reward: $material x$quantity");
                        }
                    }
                }
            }

            // Get FINAL data after ALL updates
            $finalData = CharacterConfrontingDeath::getData($characterId);
            Log::info("ConfrontingDeath AFTER battle: Energy {$finalData['energy']}, Battles {$finalData['total_battles']}");

            return [
                'status'         => 1,
                'error'          => 0,
                'result'         => [
                    (int)$xpEarned,
                    (int)$goldEarned,
                    $materials
                ],
                'level'          => (int)$character->level,
                'xp'             => (int)$character->xp,
                'level_up'       => $levelUp,
                'total_battles'  => (int)$finalData['total_battles'],
                'energy'         => (int)$finalData['energy']
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath finishBattle Error: " . $e->getMessage());
            Log::error("ConfrontingDeath finishBattle Stack: " . $e->getTraceAsString());
            return ['status' => 0, 'error' => 'Failed to finish battle: ' . $e->getMessage()];
        }
    }

    /**
     * Get bonus rewards status (milestone)
     */
    public function getBonusRewards($characterId, $sessionkey)
    {
        try {
            Log::info("ConfrontingDeath getBonusRewards: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $data = CharacterConfrontingDeath::getData($characterId);

            // Return milestone status
            $rewards = [];
            foreach ($data['milestone_data'] as $milestone) {
                $rewards[] = $milestone['claimed'];
            }

            return [
                'status' => 1,
                'error' => 0,
                'milestone' => (int)$data['total_battles'],
                'rewards' => $rewards
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath getBonusRewards Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to get bonus rewards'];
        }
    }

    /**
     * Claim milestone rewards
     */
    public function claimBonusRewards($characterId, $sessionkey, $milestoneIndex)
    {
        try {
            Log::info("ConfrontingDeath claimBonusRewards: Char $characterId Index $milestoneIndex");

            $character = Character::with('user')->find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $data = CharacterConfrontingDeath::getData($characterId);

            // Validate index
            if ($milestoneIndex < 0 || $milestoneIndex >= 8) {
                return ['status' => 0, 'error' => 'Invalid milestone index'];
            }

            $milestone = $this->eventData['milestone_battle'][$milestoneIndex];

            // Check battles requirement
            if ($data['total_battles'] < $milestone['requirement']) {
                return ['status' => 0, 'error' => 'Insufficient battles'];
            }

            // Check if already claimed
            if ($data['milestone_data'][$milestoneIndex]['claimed']) {
                return ['status' => 0, 'error' => 'Reward already claimed'];
            }

            // Mark as claimed
            $milestoneData = $data['milestone_data'];
            $milestoneData[$milestoneIndex]['claimed'] = true;
            CharacterConfrontingDeath::setMilestoneData($characterId, $milestoneData);

            // Process reward
            $rewardId = str_replace('%s', $character->gender, $milestone['id']);
            $quantity = $milestone['quantity'];

            // Add reward
            $this->addRewardToCharacter($character, $rewardId, $quantity);

            Log::info("ConfrontingDeath Milestone Claimed: Index $milestoneIndex Reward $rewardId");

            return [
                'status' => 1,
                'error' => 0,
                'reward' => [$rewardId]
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath claimBonusRewards Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to claim reward'];
        }
    }

    /**
     * Buy skill from training
     */
    public function buySkill($characterId, $sessionkey, $skillIndex)
    {
        try {
            Log::info("ConfrontingDeath buySkill: Char $characterId Index $skillIndex");

            $character = Character::with('user')->find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Validate skill index
            if ($skillIndex < 0 || $skillIndex >= count($this->eventData['training'])) {
                return ['status' => 0, 'error' => 'Invalid skill index'];
            }

            $skill = $this->eventData['training'][$skillIndex];
            $accountType = $character->user->account_type ?? 0;
            $price = $skill['price'][$accountType == 1 ? 1 : 0];

            // Check if already has skill
            if (CharacterSkill::where('character_id', $characterId)->where('skill_id', $skill['id'])->exists()) {
                return ['status' => 0, 'error' => 'Skill already owned'];
            }

            // Check tokens
            if ($character->user->tokens < $price) {
                return ['status' => 0, 'error' => 'Insufficient tokens'];
            }

            // Deduct tokens
            $character->user->tokens -= $price;
            $character->user->save();

            // Add skill
            CharacterSkill::create([
                'character_id' => $character->id,
                'skill_id' => $skill['id']
            ]);

            // Special logic: If buying skill_2314 (index 1), also add skill_2313 (index 0)
            if ($skillIndex == 1) {
                CharacterSkill::firstOrCreate([
                    'character_id' => $character->id,
                    'skill_id' => $this->eventData['training'][0]['id']
                ]);
                Log::info("ConfrontingDeath: Also added prerequisite skill {$this->eventData['training'][0]['id']}");
            }

            Log::info("ConfrontingDeath Skill Bought: {$skill['id']} for $price tokens");

            return [
                'status' => 1,
                'error' => 0,
                'skill_id' => $skill['id']
            ];

        } catch (\Exception $e) {
            Log::error("ConfrontingDeath buySkill Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to buy skill'];
        }
    }

    /**
     * Add reward to character
     */
    private function addRewardToCharacter($character, $rewardId, $quantity)
    {
        // Handle gold
        if (strpos($rewardId, 'gold_') === 0) {
            $amount = (int)str_replace('gold_', '', $rewardId);
            $character->gold += $amount;
            $character->save();
            return;
        }

        // Handle tokens
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

    /**
     * Get category from item ID
     */
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
}