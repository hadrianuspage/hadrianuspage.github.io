<?php

namespace App\Services\Amf\AdvanceAcademyService;

use App\Models\Character;
use App\Models\CharacterSkill;
use App\Models\Skill;
use App\Models\User;
use App\Models\GameConfig;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class UpgradeService
{
    use ValidatesSession;

    /**
     * upgradeSkill
     * Params: [charId, sessionKey, nextSkillId]
     */
    public function upgradeSkill($charId, $sessionKey, $nextSkillId)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF AdvanceAcademy.upgradeSkill: Char $charId to $nextSkillId");

        try {
            return DB::transaction(function () use ($charId, $nextSkillId) {
                $char = Character::lockForUpdate()->find($charId);
                if (!$char) return ['status' => 0, 'error' => 'Character not found'];

                $user = User::lockForUpdate()->find($char->user_id);
                if (!$user) return ['status' => 0, 'error' => 'User not found'];

                // 1. Get Skill Info - AUTO-CREATE jika tidak ada
                $skill = Skill::where('skill_id', $nextSkillId)->first();
                if (!$skill) {
                    $skill = $this->createDefaultSkill($nextSkillId);
                    if (!$skill) {
                        Log::warning("Skill not found in database or library: $nextSkillId");
                        return ['status' => 2, 'result' => 'Skill info not found!'];
                    }
                }

                // 2. Identify the current skill ID being replaced
                $currentSkillId = $this->findCurrentSkillId($nextSkillId);
                
                // Debug log
                Log::info("Upgrade mapping: $nextSkillId <- $currentSkillId");

                // 3. Verify Ownership of previous version (if any)
                if ($currentSkillId) {
                    if (!CharacterSkill::where('character_id', $char->id)->where('skill_id', $currentSkillId)->exists()) {
                        return ['status' => 2, 'result' => 'You do not own the prerequisite skill!'];
                    }
                }

                // 4. Check Level and Cost
                if ($char->level < $skill->level) {
                    return ['status' => 2, 'result' => "Level {$skill->level} required!"];
                }

                if ($user->tokens < $skill->price_tokens) {
                    return ['status' => 2, 'result' => 'Not enough tokens!'];
                }

                if ($char->gold < $skill->price_gold) {
                    return ['status' => 2, 'result' => 'Not enough gold!'];
                }

                // 5. Execute Upgrade
                $user->tokens -= $skill->price_tokens;
                $user->save();

                $char->gold -= $skill->price_gold;

                // Remove old skill
                if ($currentSkillId) {
                    CharacterSkill::where('character_id', $char->id)->where('skill_id', $currentSkillId)->delete();
                }

                // Add new skill
                CharacterSkill::firstOrCreate([
                    'character_id' => $char->id,
                    'skill_id' => $nextSkillId
                ]);

                // 6. Update Equipment if necessary
                $equipped = explode(',', $char->equipment_skills);
                $updatedEquipped = false;
                if ($currentSkillId) {
                    foreach ($equipped as $idx => $id) {
                        if ($id === $currentSkillId) {
                            $equipped[$idx] = $nextSkillId;
                            $updatedEquipped = true;
                        }
                    }
                }
                if ($updatedEquipped) {
                    $char->equipment_skills = implode(',', $equipped);
                }

                $char->save();

                // 7. Prepare response
                $equippedSkillsStr = $char->equipment_skills;

                return [
                    'status' => 1,
                    'result' => 'Skill upgraded successfully!',
                    'account_tokens' => (int)$user->tokens,
                    'character_gold' => (int)$char->gold,
                    'character_skills' => $equippedSkillsStr,
                    'character_set_skills' => $equippedSkillsStr
                ];
            });

        } catch (\Exception $e) {
            Log::error("Upgrade Skill Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Internal Server Error'];
        }
    }

    /**
     * Find current skill ID yang akan di-replace
     */
    private function findCurrentSkillId($nextSkillId)
    {
        // 1. Cek dari academy_chains config
        $chains = GameConfig::get('academy_chains', []);
        
        if (!empty($chains)) {
            foreach ($chains as $element => $elementChains) {
                foreach ($elementChains as $chainName => $skillIds) {
                    if (in_array($nextSkillId, $skillIds)) {
                        $idx = array_search($nextSkillId, $skillIds);
                        if ($idx > 0) {
                            return $skillIds[$idx - 1];
                        }
                        // Jika index 0, berarti ini skill pertama (tidak ada prerequisite)
                        return null;
                    }
                }
            }
        }

        // 2. Fallback: Pattern matching untuk skill upgrade
        $upgradePatterns = $this->getUpgradePatterns();
        return $upgradePatterns[$nextSkillId] ?? null;
    }

    /**
     * Fallback upgrade patterns jika config tidak ada
     */
    private function getUpgradePatterns()
    {
        return [
            // Kinjutsu upgrades
            'skill_kinjutsu_evasion_2' => 'skill_kinjutsu_evasion_1',
            'skill_kinjutsu_evasion_3' => 'skill_kinjutsu_evasion_2',
            'skill_kinjutsu_counter_2' => 'skill_kinjutsu_counter_1',
            'skill_kinjutsu_counter_3' => 'skill_kinjutsu_counter_2',
            
            // Taijutsu upgrades
            'skill_taijutsu_power_2' => 'skill_taijutsu_power_1',
            'skill_taijutsu_power_3' => 'skill_taijutsu_power_2',
            'skill_taijutsu_speed_2' => 'skill_taijutsu_speed_1',
            'skill_taijutsu_speed_3' => 'skill_taijutsu_speed_2',
            
            // Ninjutsu upgrades
            'skill_ninjutsu_fire_2' => 'skill_ninjutsu_fire_1',
            'skill_ninjutsu_fire_3' => 'skill_ninjutsu_fire_2',
            'skill_ninjutsu_water_2' => 'skill_ninjutsu_water_1',
            'skill_ninjutsu_water_3' => 'skill_ninjutsu_water_2',
            'skill_ninjutsu_earth_2' => 'skill_ninjutsu_earth_1',
            'skill_ninjutsu_earth_3' => 'skill_ninjutsu_earth_2',
            'skill_ninjutsu_lightning_2' => 'skill_ninjutsu_lightning_1',
            'skill_ninjutsu_lightning_3' => 'skill_ninjutsu_lightning_2',
            'skill_ninjutsu_wind_2' => 'skill_ninjutsu_wind_1',
            'skill_ninjutsu_wind_3' => 'skill_ninjutsu_wind_2',
            
            // Genjutsu upgrades
            'skill_genjutsu_illusion_2' => 'skill_genjutsu_illusion_1',
            'skill_genjutsu_illusion_3' => 'skill_genjutsu_illusion_2',
            'skill_genjutsu_mind_2' => 'skill_genjutsu_mind_1',
            'skill_genjutsu_mind_3' => 'skill_genjutsu_mind_2',
            
            // Medical upgrades
            'skill_medical_healing_2' => 'skill_medical_healing_1',
            'skill_medical_healing_3' => 'skill_medical_healing_2',
            'skill_medical_support_2' => 'skill_medical_support_1',
            'skill_medical_support_3' => 'skill_medical_support_2',
        ];
    }

    /**
     * Helper: Auto-create skill dari library jika tidak ada
     */
    private function createDefaultSkill($skillId)
    {
        $skillData = $this->getLibrarySkill($skillId);
        if ($skillData) {
            $skill = Skill::create([
                'skill_id' => $skillId,
                'name' => $skillData['name'] ?? 'Unknown Skill',
                'level' => $skillData['level'] ?? 1,
                'element' => $skillData['element'] ?? 0,
                'price_gold' => $skillData['price_gold'] ?? 0,
                'price_tokens' => $skillData['price_tokens'] ?? 0,
                'premium' => $skillData['premium'] ?? false,
                'icon' => $skillData['icon'] ?? null,
            ]);
            
            Log::info("Created skill from library for upgrade: $skillId");
            return $skill;
        }
        
        return null;
    }

    /**
     * Helper: Load skill dari skills.json
     */
    private function getLibrarySkill($skillId)
    {
        static $skillsIndex = null;
        
        if ($skillsIndex === null) {
            $skillsPath = base_path('public/game_data/skills.json');
            if (file_exists($skillsPath)) {
                $raw = file_get_contents($skillsPath);
                $skills = json_decode($raw, true);
                $skillsIndex = [];
                if (is_array($skills)) {
                    foreach ($skills as $skill) {
                        if (isset($skill['id'])) {
                            $skillsIndex[$skill['id']] = $skill;
                        }
                    }
                }
            } else {
                $skillsIndex = [];
            }
        }
        
        return $skillsIndex[$skillId] ?? null;
    }
}