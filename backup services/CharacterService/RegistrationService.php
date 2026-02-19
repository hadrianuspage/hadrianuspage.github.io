<?php

namespace App\Services\Amf\CharacterService;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use App\Models\User;
use App\Models\XP;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class RegistrationService
{
    use ValidatesSession;

    /**
     * characterRegister
     */
    public function characterRegister($params)
    {
        $accountId = $params[0];
        $sessionKeyHash = $params[1];
        $charName = $params[2];
        $gender = $params[3];
        $element = $params[4];
        $hairColor = $params[5];
        $hairNum = $params[6];

        Log::info("AMF Character Register: $charName for User $accountId Element $element");

        // $guard = $this->guardUserSession((int)$accountId, $sessionKeyHash);
        // if ($guard) {
        //     return $guard;
        // }

        if (strlen($charName) < 2) {
            return ['status' => 2, 'error' => 'Character name too short.'];
        }

        if (Character::where('name', $charName)->exists()) {
            return ['status' => 2, 'error' => 'Character name already taken.'];
        }

        $user = User::find($accountId);
        if (!$user) return ['status' => 0, 'error' => 'User not found.'];

        $characterCount = Character::where('user_id', $accountId)->count();
        $maxCharacters = ($user->account_type == 1) ? 6 : 1;

        if ($characterCount >= $maxCharacters) {
            return [
                'status' => 2,
                'result' => ($user->account_type == 1)
                    ? 'You have reached the maximum limit of 6 characters.'
                    : 'Free users can only create 1 character. Upgrade to Premium for 6 slots!'
            ];
        }

        try {
            $elementSkillMap = [
                1 => 'skill_13', // Wind
                2 => 'skill_10', // Fire
                3 => 'skill_01', // Lightning
                4 => 'skill_12', // Water
                5 => 'skill_09', // Earth
            ];

            $basicSkill = $elementSkillMap[$element] ?? 'skill_01';
            $genderSuffix = $gender == 0 ? '_0' : '_1';
            
            // Default skills: element skill + skill_718
            $defaultSkills = [$basicSkill, 'skill_718'];

            // Calculate XP needed to reach level 5
            $xpForLevel5 = $this->calculateXpForLevel(5);

            // KEEP ORIGINAL CHARACTER CREATE - ONLY ADD LEVEL/XP/GOLD/POINTS
            $character = Character::create([
                'user_id' => $accountId,
                'name' => $charName,
                'level' => 5, // NEW: Start at level 5
                'xp' => $xpForLevel5, // NEW: XP to reach level 5
                'gender' => $gender,
                'element_1' => $element,
                'hair_style' => 'hair_' . str_pad($hairNum, 2, '0', STR_PAD_LEFT) . $genderSuffix,
                'hair_color' => $hairColor,
                'point_free' => 21, // NEW: 1 base + 20 from levels (4 levels × 5 points)
                'gold' => 5000, // NEW: Bonus starting gold (was 1000)
                'equipment_weapon' => 'wpn_01',
                'equipment_back' => 'back_01',
                'equipment_clothing' => 'set_01' . $genderSuffix,
                'equipment_accessory' => 'accessory_01',
                'equipment_skills' => implode(',', $defaultSkills), // NEW: Added skill_718
            ]);

            // Add skills to character_skills table
            foreach ($defaultSkills as $s) {
                CharacterSkill::create([
                    'character_id' => $character->id,
                    'skill_id' => $s
                ]);
            }

            // Add default items (KEEP ORIGINAL)
            $defaults = [
                ['id' => 'wpn_01', 'cat' => 'weapon'],
                ['id' => 'back_01', 'cat' => 'back'],
                ['id' => 'accessory_01', 'cat' => 'accessory'],
                ['id' => 'set_01' . $genderSuffix, 'cat' => 'set'],
            ];

            foreach ($defaults as $d) {
                CharacterItem::create([
                    'character_id' => $character->id,
                    'item_id' => $d['id'],
                    'quantity' => 1,
                    'category' => $d['cat']
                ]);
            }

            Log::info("Character created: {$character->id} - Level 5 with {$xpForLevel5} XP, 21 stat points, 5000 gold, skills: " . implode(', ', $defaultSkills));

            return ['status' => 1];

        } catch (\Exception $e) {
            Log::error("Character Creation Error: " . $e->getMessage());
            return [
                'status' => 0,
                'error' => 'Internal Server Error'
            ];
        }
    }

    /**
     * Calculate XP needed to reach a specific level
     */
    private function calculateXpForLevel(int $targetLevel): int
    {
        if ($targetLevel <= 1) {
            return 0;
        }

        $totalXp = 0;
        
        // Sum up XP requirements from level 1 to target level
        for ($level = 1; $level < $targetLevel; $level++) {
            $xpReq = XP::where('level', $level)->value('character_xp');
            $totalXp += $xpReq ?: ($level * 100); // Fallback formula if XP table is missing
        }

        return $totalXp;
    }
}