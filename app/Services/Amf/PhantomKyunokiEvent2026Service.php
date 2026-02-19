<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use App\Models\CharacterPhantomKyunoki;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class PhantomKyunokiEvent2026Service
{
    private const REFILL_PRICE = 50;
    private const MAX_ENERGY = 8;

    /**
     * Static event data - FIXED VALUES
     */
    private $eventData = [
        'bosses' => [
            'id' => ['ene_258', 'ene_256', 'ene_257'],
            'name' => 'Phantom Kyunoki',
            'description' => 'Phantom Kyunoki is a ghost that is known for its ability to use phantom energy to attack its enemies.',
            'levels' => [0, 5],
            'gold' => 2500,
            'xp' => 2500,
            'rewards' => ['material_2232', 'material_2233', 'material_2234', 'material_2235', 'tokens_5'],
            'background' => 'mission_1066'
        ],
        'training' => [
            [
                'id' => 'skill_2333',
                'price' => [6499, 4999],
                'name' => "Kinjutsu: Kyunoki's Falling Omen"
            ]
        ],
        'milestone_battle' => [
            ['id' => 'tokens_150', 'requirement' => 50, 'quantity' => 1],
            ['id' => 'set_716_%s', 'requirement' => 100, 'quantity' => 1],
            ['id' => 'skill_484', 'requirement' => 200, 'quantity' => 1],
            ['id' => 'essential_10', 'requirement' => 300, 'quantity' => 1]
        ]
    ];

    public function getBattleData($characterId, $sessionkey)
    {
        try {
            Log::info("PhantomKyunoki getBattleData: Char $characterId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Auto refill energy berdasarkan waktu
            $data = CharacterPhantomKyunoki::autoRefillEnergy($characterId);

            Log::info("PhantomKyunoki Data: Energy {$data['energy']}, Kills {$data['total_kills']}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => $data['energy'],
                'total_kills' => $data['total_kills'],
                'milestone_data' => $data['milestone_data'],
                'next_energy_time' => CharacterPhantomKyunoki::getNextEnergyTime($characterId)
            ];

        } catch (\Exception $e) {
            Log::error("PhantomKyunoki getBattleData Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to get battle data'];
        }
    }

    public function refillEnergy($characterId, $sessionkey)
    {
        try {
            Log::info("PhantomKyunoki refillEnergy: Char $characterId");

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
            $data = CharacterPhantomKyunoki::refillEnergyWithToken($characterId);

            Log::info("PhantomKyunoki Energy Refilled with Token: New energy {$data['energy']}");

            return [
                'status' => 1,
                'error' => 0,
                'energy' => $data['energy']
            ];

        } catch (\Exception $e) {
            Log::error("PhantomKyunoki refillEnergy Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to refill energy'];
        }
    }

    public function startBattle($characterId, $bossId, $agility, $enemyData, $hash, $sessionkey)
    {
        try {
            Log::info("PhantomKyunoki startBattle: Char $characterId Boss $bossId");

            $character = Character::find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            // Auto refill energy berdasarkan waktu
            $data = CharacterPhantomKyunoki::autoRefillEnergy($characterId);

            // Check energy - TIDAK mengurangi energy di sini
            if ($data['energy'] <= 0) {
                return ['status' => 0, 'error' => 'Insufficient energy'];
            }

            // Generate battle code
            $battleCode = 'PK' . time() . rand(1000, 9999);

            // Generate response hash
            $responseHash = hash('sha256', $bossId . $battleCode . $characterId);

            Log::info("PhantomKyunoki Battle Started: Code $battleCode, Current Energy: {$data['energy']}");

            return [
                'status' => 1,
                'error' => 0,
                'code' => $battleCode,
                'hash' => $responseHash
            ];

        } catch (\Exception $e) {
            Log::error("PhantomKyunoki startBattle Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to start battle'];
        }
    }

   public function finishBattle($characterId, $bossId, $won, $sessionkey)
{
    try {
        // FIXED: Force win for testing
        $wonBool = true;
        
        Log::info("PhantomKyunoki finishBattle START: Char $characterId Boss $bossId");

        $character = Character::find($characterId);
        if (!$character) {
            return ['status' => 0, 'error' => 'Character not found'];
        }

        // Get current data BEFORE any changes
        $beforeData = CharacterPhantomKyunoki::getData($characterId);
        Log::info("PhantomKyunoki BEFORE battle: Energy {$beforeData['energy']}, Kills {$beforeData['total_kills']}");

        // Auto refill energy berdasarkan waktu
        $data = CharacterPhantomKyunoki::autoRefillEnergy($characterId);

        // Check energy availability
        if ($data['energy'] <= 0) {
            Log::warning("PhantomKyunoki finishBattle: No energy available");
            return ['status' => 0, 'error' => 'No energy available'];
        }

        // KURANGI ENERGY DI SINI (setelah battle selesai)
        $energyUsed = CharacterPhantomKyunoki::useEnergy($characterId, 1);
        
        if (!$energyUsed) {
            Log::error("PhantomKyunoki finishBattle: Failed to use energy");
            return ['status' => 0, 'error' => 'Failed to use energy'];
        }

        // Get boss data
        $bossData = $this->eventData['bosses'];
        Log::info("PhantomKyunoki: Boss data - Gold: {$bossData['gold']}, XP: {$bossData['xp']}");

        $goldEarned = 0;
        $xpEarned   = 0;
        $materials  = [];
        $levelUp    = false;

        if ($wonBool) {
            $goldEarned = (int)$bossData['gold'];
            $xpEarned   = (int)$bossData['xp'];

            // Increment kill count - PENTING!
            CharacterPhantomKyunoki::incrementKills($characterId);

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
                        Log::info("PhantomKyunoki Reward: $material x$quantity");
                    }
                }
            }
        }

        // Get FINAL data after ALL updates
        $finalData = CharacterPhantomKyunoki::getData($characterId);
        Log::info("PhantomKyunoki AFTER battle: Energy {$finalData['energy']}, Kills {$finalData['total_kills']}");

        // FORMAT SAMA PERSIS SEPERTI ThanksGiving finishBattle
        return [
            'status'       => 1,
            'error'        => 0,
            'result'       => [
                (int)$xpEarned,
                (int)$goldEarned,
                $materials
            ],
            'level'        => (int)$character->level,
            'xp'           => (int)$character->xp,
            'level_up'     => $levelUp,
            'total_kills'  => (int)$finalData['total_kills'],
            'energy'       => (int)$finalData['energy'],
        ];

    } catch (\Exception $e) {
        Log::error("PhantomKyunoki finishBattle Error: " . $e->getMessage());
        Log::error("PhantomKyunoki finishBattle Stack: " . $e->getTraceAsString());
        return ['status' => 0, 'error' => 'Failed to finish battle: ' . $e->getMessage()];
    }
}

    public function claimBonusRewards($characterId, $sessionkey, $milestoneIndex)
    {
        try {
            Log::info("PhantomKyunoki claimBonusRewards: Char $characterId Index $milestoneIndex");

            $character = Character::with('user')->find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $data = CharacterPhantomKyunoki::getData($characterId);

            // Validate index
            if ($milestoneIndex < 0 || $milestoneIndex >= 4) {
                return ['status' => 0, 'error' => 'Invalid milestone index'];
            }

            $milestone = $this->eventData['milestone_battle'][$milestoneIndex];

            // Check kills requirement
            if ($data['total_kills'] < $milestone['requirement']) {
                return ['status' => 0, 'error' => 'Insufficient kills'];
            }

            // Check if already claimed
            if ($data['milestone_data'][$milestoneIndex]['claimed']) {
                return ['status' => 0, 'error' => 'Reward already claimed'];
            }

            // Mark as claimed
            $milestoneData = $data['milestone_data'];
            $milestoneData[$milestoneIndex]['claimed'] = true;
            CharacterPhantomKyunoki::setMilestoneData($characterId, $milestoneData);

            // Process reward
            $rewardId = str_replace('%s', $character->gender, $milestone['id']);
            $quantity = $milestone['quantity'];

            // Add reward
            $this->addRewardToCharacter($character, $rewardId, $quantity);

            Log::info("PhantomKyunoki Milestone Claimed: Index $milestoneIndex Reward $rewardId");

            return [
                'status' => 1,
                'error' => 0,
                'reward' => [$rewardId]
            ];

        } catch (\Exception $e) {
            Log::error("PhantomKyunoki claimBonusRewards Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to claim reward'];
        }
    }

    public function buyPackage($characterId, $sessionkey)
    {
        try {
            Log::info("PhantomKyunoki buyPackage: Char $characterId");

            $character = Character::with('user')->find($characterId);
            if (!$character) {
                return ['status' => 0, 'error' => 'Character not found'];
            }

            $skill = $this->eventData['training'][0];
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

            // Deduct tokens and add skill
            $character->user->tokens -= $price;
            $character->user->save();

            $this->addRewardToCharacter($character, $skill['id'], 1);

            Log::info("PhantomKyunoki Package Bought: Skill {$skill['id']} Price $price");

            return [
                'status' => 1,
                'error' => 0,
                'skill_id' => $skill['id']
            ];

        } catch (\Exception $e) {
            Log::error("PhantomKyunoki buyPackage Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Failed to buy package'];
        }
    }

    private function addRewardToCharacter($character, $rewardId, $quantity)
    {
        // Handle special rewards
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
}

