<?php

namespace App\Services\Amf\DailyScratchService;

use App\Models\Character;
use App\Models\CharacterPet;
use App\Models\CharacterSkill;
use App\Services\Amf\Concerns\ValidatesSession;
use App\Services\Amf\RewardGrantService;
use Illuminate\Support\Facades\Log;

class ScratchService
{
    use ValidatesSession;

    /**
     * scratch
     * Params: [charId, sessionKey]
     */
    public function scratch($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF DailyScratch.scratch: Char $charId");

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        // Recalculate max tickets based on consecutive days
        // Free: 1 ticket. Premium: base 1 + consecutive day bonus
        $isPremium = $char->user && $char->user->account_type == 1;
        $maxTickets = $isPremium ? (1 + (int) $char->daily_scratch_consecutive) : 1;

        if ($char->daily_scratch_count >= $maxTickets) {
            return ['status' => 2, 'result' => 'No tickets left!'];
        }

        // Pick Reward
        $rewardStr = $this->pickReward($char);
        if (!$rewardStr) {
            Log::error('AMF DailyScratch.scratch: No valid reward available', [
                'char_id' => $char->id,
                'config' => $this->getRewardsConfig()
            ]);
            return ['status' => 0, 'error' => 'Invalid scratch reward config'];
        }

        Log::info('AMF DailyScratch.scratch: Reward picked', [
            'char_id' => $char->id,
            'reward' => $rewardStr
        ]);

        // Grant Reward
        try {
            $this->grantReward($char, $rewardStr);
            $char->daily_scratch_count++;
            $char->save();
        } catch (\Exception $e) {
            Log::error('AMF DailyScratch.scratch: Failed to grant reward', [
                'char_id' => $char->id,
                'reward' => $rewardStr,
                'error' => $e->getMessage()
            ]);
            return ['status' => 0, 'error' => 'Failed to grant reward'];
        }

        // Format reward untuk client
        $clientReward = $this->formatRewardForClient($rewardStr);

        Log::info('AMF DailyScratch.scratch: Reward formatted', [
            'char_id' => $char->id,
            'original_reward' => $rewardStr,
            'client_reward' => $clientReward
        ]);

        return [
            'status' => 1,
            'reward' => $clientReward
        ];
    }

    /**
     * Format reward string untuk client
     */
    private function formatRewardForClient(string $rewardStr): string
    {
        // Parse reward string
        $parts = explode('_', $rewardStr);
        
        if (count($parts) < 2) {
            return $rewardStr; // Return original jika format tidak sesuai
        }

        $type = $parts[0];
        $value = $parts[1];

        // Handle special cases
        switch ($type) {
            case 'xp':
                // Handle xp_percent_10 -> return "xp_10" untuk client
                if (isset($parts[1]) && $parts[1] === 'percent' && isset($parts[2])) {
                    return "xp_" . $parts[2];
                }
                break;
                
            case 'tokens':
                // tokens_80 -> return "tokens_80"
                return $rewardStr;
                
            case 'gold':
                // gold_500000 -> return "gold_500000"
                return $rewardStr;
                
            case 'tp':
                // tp_2000 -> return "tp_2000"  
                return $rewardStr;
                
            case 'item':
                // item_mini_talent_pill -> return "item_mini_talent_pill"
                return $rewardStr;
                
            case 'wpn':
                // wpn_shinobu -> return "wpn_shinobu"
                return $rewardStr;
                
            case 'back':
                // back_musket -> return "back_musket"
                return $rewardStr;
                
            case 'accessory':
                // accessory_silver_wolf -> return "accessory_silver_wolf"
                return $rewardStr;
                
            case 'pet':
                // pet_syrup -> return "pet_syrup"
                return $rewardStr;
                
            case 'skill':
                // skill_fan_god -> return "skill_fan_god"
                return $rewardStr;
        }

        return $rewardStr; // Default return original
    }

    /**
     * getRewards
     */
    private function getRewardsConfig(): array
    {
        // Coba ambil dari config 'scratch' dulu
        $config = \App\Models\GameConfig::where('key', 'scratch')->first();
        
        if ($config && !empty($config->value)) {
            $decoded = is_string($config->value) ? json_decode($config->value, true) : $config->value;
            
            if (is_array($decoded)) {
                if (isset($decoded['rewards']) && is_array($decoded['rewards'])) {
                    return $decoded;
                }
                if (array_is_list($decoded)) {
                    return ['rewards' => $decoded];
                }
            }
        }

        // Fallback ke config 'scratch_rewards'
        $legacyConfig = \App\Models\GameConfig::where('key', 'scratch_rewards')->first();
        
        if ($legacyConfig && !empty($legacyConfig->value)) {
            $decoded = is_string($legacyConfig->value) ? json_decode($legacyConfig->value, true) : $legacyConfig->value;
            
            if (is_array($decoded)) {
                return ['rewards' => $decoded];
            }
        }

        // Hardcoded fallback jika tidak ada config
        return [
            'rewards' => [
                'tokens_80',
                'gold_500000',
                'xp_percent_10',
                'tp_2000',
                'item_mini_talent_pill',
                'item_small_talent_pill',
                'item_moyai_coin',
                'item_ninja_seal_gan',
                'item_ninja_blood_gan',
                'item_rename_badge',
                'wpn_shinobu',
                'wpn_wicked',
                'wpn_yakumo',
                'back_musket',
                'back_shadow_twin',
                'accessory_silver_wolf',
                'pet_syrup',
                'skill_fan_god'
            ]
        ];
    }

    private function pickReward(Character $char): ?string
    {
        $config = $this->getRewardsConfig();
        $rewards = $config['rewards'] ?? [];
        $grandRewards = $config['grand_prize'] ?? [];

        if (!is_array($rewards) || empty($rewards)) {
            Log::error('AMF DailyScratch: No rewards configured', ['config' => $config]);
            return 'gold_10000'; // Return fallback instead of null
        }

        // Log untuk debugging
        Log::info('AMF DailyScratch pickReward', [
            'char_id' => $char->id,
            'total_rewards' => count($rewards),
            'rewards' => $rewards
        ]);

        $eligibleRewards = $this->filterOwnedRewards($char, $rewards);
        
        // Jika tidak ada reward yang eligible, return fallback
        if (empty($eligibleRewards)) {
            Log::warning('AMF DailyScratch: No eligible rewards', ['char_id' => $char->id]);
            // Return default reward
            return 'gold_10000';
        }

        $rareRewards = array_filter($eligibleRewards, function ($reward) {
            return is_string($reward) && (str_starts_with($reward, 'pet_') || str_starts_with($reward, 'skill_') || str_starts_with($reward, 'wpn_') || str_starts_with($reward, 'back_') || str_starts_with($reward, 'accessory_'));
        });

        $commonRewards = array_values(array_diff($eligibleRewards, $rareRewards));

        $grandProgress = (int) ($char->scratch_grand_progress ?? 0) + 1;
        $rareProgress = (int) ($char->scratch_rare_progress ?? 0) + 1;

        // Grand Prize Logic
        if (!empty($grandRewards) && $this->shouldGrantGrandPrize($grandProgress, $grandRewards)) {
            $char->scratch_grand_progress = 0;
            $char->scratch_rare_progress = $rareProgress;
            $char->save();
            return $this->randomReward($grandRewards) ?? 'gold_10000';
        }

        // Rare Prize Logic
        if (!empty($rareRewards) && $this->shouldGrantRarePrize($rareProgress, $rareRewards)) {
            $char->scratch_grand_progress = $grandProgress;
            $char->scratch_rare_progress = 0;
            $char->save();
            return $this->randomReward($rareRewards) ?? 'gold_10000';
        }

        // Common Rewards
        $char->scratch_grand_progress = $grandProgress;
        $char->scratch_rare_progress = $rareProgress;
        $char->save();

        if (!empty($commonRewards)) {
            return $this->randomReward($commonRewards) ?? 'gold_10000';
        }

        // Fallback to any eligible reward
        return $this->randomReward($eligibleRewards) ?? 'gold_10000';
    }

    private function filterOwnedRewards(Character $char, array $rewards): array
    {
        $filtered = [];

        foreach ($rewards as $reward) {
            if (!is_string($reward)) {
                continue;
            }
            
            // Check pet ownership
            if (str_starts_with($reward, 'pet_')) {
                $petId = $reward;
                if ($char->pets()->where('pet_id', $petId)->exists()) {
                    continue; // Skip if already owned
                }
            }
            
            // Check skill ownership
            if (str_starts_with($reward, 'skill_')) {
                $skillId = $reward;
                if ($char->skills()->where('skill_id', $skillId)->exists()) {
                    continue; // Skip if already owned
                }
            }
            
            $filtered[] = $reward;
        }

        return $filtered;
    }

    private function shouldGrantGrandPrize(int $progress, array $grandRewards): bool
    {
        if (empty($grandRewards)) {
            return false;
        }
        if ($progress < 100) {
            return false;
        }
        if ($progress >= 500) {
            return true;
        }

        $chance = ($progress - 100) / 400; // 0.0 - 1.0 from 100 to 500
        return $this->rollChance($chance);
    }

    private function shouldGrantRarePrize(int $progress, array $rareRewards): bool
    {
        if (empty($rareRewards)) {
            return false;
        }
        if ($progress < 50) {
            return false;
        }
        if ($progress >= 200) {
            return true;
        }

        $chance = ($progress - 50) / 150; // 0.0 - 1.0 from 50 to 200
        return $this->rollChance($chance);
    }

    private function rollChance(float $chance): bool
    {
        $chance = max(0.0, min(1.0, $chance));
        return random_int(1, 10000) <= (int) round($chance * 10000);
    }

    private function randomReward(array $rewards): ?string
    {
        if (empty($rewards)) {
            return null;
        }
        $reward = $rewards[array_rand($rewards)];
        return is_string($reward) ? $reward : null;
    }

    private function grantReward($char, $rewardStr)
    {
        (new RewardGrantService())->grant($char, $rewardStr);
    }
}