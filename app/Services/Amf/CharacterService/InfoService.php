<?php

namespace App\Services\Amf\CharacterService;

use App\Models\Character;
use App\Models\CharacterFriend;
use App\Models\CharacterPet;
use App\Models\CharacterTalent;
use App\Models\Pet;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class InfoService
{
    use ValidatesSession;

    /**
     * Resolve pet skills dengan format fixed 6 digit
     * Skill terbuka disesuaikan dengan total skills yang dimiliki pet
     */
    private function resolvePetSkills($activePet, ?Pet $petConfig): string
    {
        $petInfo = Pet::getPetInfo($activePet->pet_id);
        $totalSkills = $petInfo['total_skills'];
        $level = (int)$activePet->level;
        
        // Hitung berapa skills yang sudah terbuka berdasarkan level
        $unlockLevels = $petInfo['unlock_levels'];
        $unlockedCount = 0;
        
        foreach ($unlockLevels as $requiredLevel) {
            if ($level >= $requiredLevel) {
                $unlockedCount++;
            } else {
                break; // Stop at first locked skill
            }
        }
        
        // Pastikan tidak melebihi total skills yang dimiliki
        $unlockedCount = min($unlockedCount, $totalSkills);
        
        // Format: 6 digit fixed, skill terbuka sesuai unlockedCount
        $skillsArray = [0, 0, 0, 0, 0, 0]; // Default semua locked
        for ($i = 0; $i < $unlockedCount; $i++) {
            $skillsArray[$i] = 1;
        }
        
        return implode(',', $skillsArray);
    }

    public function getInfo($charId, $sessionKey, $targetId, $type)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF Get Info: Char $charId Target $targetId Type $type");

        $char = Character::with('user')->find($targetId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        $genderSuffix = ($char->gender == 0 ? '_0' : '_1');

        if (is_numeric($char->hair_style)) {
            $hairstyle = 'hair_' . str_pad($char->hair_style, 2, '0', STR_PAD_LEFT) . $genderSuffix;
        } else {
            $hairstyle = $char->hair_style ?: 'hair_01' . $genderSuffix;
        }

        $elementSkillMap = [
            1 => 'skill_13', 2 => 'skill_10', 3 => 'skill_01',
            4 => 'skill_12', 5 => 'skill_09',
        ];
        $defaultSkill   = $elementSkillMap[$char->element_1] ?? 'skill_01';
        $equippedSkills = $char->equipment_skills ?: $defaultSkill;

        // Talent Skills
        $talents     = CharacterTalent::where('character_id', $targetId)->get();
        $talentParts = [];
        foreach ($talents as $t) {
            $talentParts[] = $t->skill_id . ":" . $t->level;
        }
        $talentSkillsStr = implode(',', $talentParts);

        // ============================================================
        // PET DATA - Auto Detection System
        // ============================================================
        $petData       = ['pet' => 0];
        $petEquippedId = 0;

        if (!empty($char->equipment_pet)) {
            $activePet = CharacterPet::where('character_id', $targetId)
                ->where('id', $char->equipment_pet)
                ->first();

            if ($activePet) {
                // Hapus prefix "pet_" untuk query ke tabel pets
                $cleanPetId = str_replace('pet_', '', $activePet->pet_id);
                $petConfig  = Pet::where('pet_id', $cleanPetId)->first();

                // ✅ Smart skills calculation - format 6 digit fixed
                $petSkillsString = $this->resolvePetSkills($activePet, $petConfig);

                // ✅ Get pet info untuk logging (auto-detect jika pet baru)
                $petInfo = Pet::getPetInfo($activePet->pet_id);

                Log::info("AMF GetInfo Pet Final", [
                    'char_id'          => $targetId,
                    'pet_instance_id'  => $activePet->id,
                    'pet_type_id_raw'  => $activePet->pet_id,
                    'pet_type_id_clean'=> $cleanPetId,
                    'pet_level'        => $activePet->level,
                    'pet_config_found' => $petConfig ? 'YES (database)' : 'NO (auto-detected)',
                    'pet_info'         => $petInfo,
                    'skills_string'    => $petSkillsString,
                    'pet_swf'          => $petConfig && $petConfig->swf ? $petConfig->swf : $activePet->pet_id,
                ]);

                $petEquippedId = $activePet->id;

                $petData = [
                    'pet'        => $activePet->id,
                    'char_id'    => (int)$targetId,
                    'pet_id'     => $activePet->pet_id,
                    'pet_name'   => $activePet->name ?: ($petConfig && $petConfig->name ? $petConfig->name : 'Pet'),
                    'pet_xp'     => (int)$activePet->xp,
                    'pet_level'  => (int)$activePet->level,
                    'pet_skills' => $petSkillsString, // ✅ Fixed 6 digit format
                    'pet_mp'     => (int)($activePet->mp ?? 100),
                    'pet_hp'     => (int)($activePet->hp ?? 100),
                    'pet_max_hp' => (int)($activePet->max_hp ?? 100),
                    'pet_max_mp' => (int)($activePet->max_mp ?? 100),
                    'pet_swf'    => $petConfig && $petConfig->swf
                                    ? $petConfig->swf
                                    : $activePet->pet_id,
                ];
            }
        }
        // ============================================================

        $charRank      = (int)$char->rank;
        $reportedLevel = $char->level;
        if ($charRank == 1 && $char->level > 20) $reportedLevel = 20;
        if ($charRank == 3 && $char->level > 40) $reportedLevel = 40;
        if ($charRank == 5 && $char->level > 60) $reportedLevel = 60;
        if ($charRank == 7 && $char->level > 80) $reportedLevel = 80;

        $isFriend = CharacterFriend::where('character_id', $charId)
            ->where('friend_id', $targetId)
            ->exists();

        return [
            'status'           => 1,
            'error'            => 0,
            'friend'           => $isFriend,
            'account_type'     => $char->user->account_type,
            'emblem_duration'  => -1,
            'events'           => (object)[],
            'has_unread_mails' => false,
            'character_data'   => [
                'character_id'         => $char->id,
                'character_name'       => $char->name,
                'character_level'      => $reportedLevel,
                'character_xp'         => $char->xp,
                'character_gender'     => $char->gender,
                'character_rank'       => $charRank,
                'character_merit'      => 0,
                'character_prestige'   => $char->prestige,
                'character_element_1'  => $char->element_1,
                'character_element_2'  => $char->element_2,
                'character_element_3'  => $char->element_3,
                'character_talent_1'   => $char->talent_1,
                'character_talent_2'   => $char->talent_2,
                'character_talent_3'   => $char->talent_3,
                'character_gold'       => $char->gold,
                'character_tp'         => $char->tp,
                'character_ss'         => $char->ss,
                'character_class'      => $char->class,
                'character_senjutsu'   => $char->senjutsu_type,
                'character_pvp_points' => 0,
            ],
            'character_points' => [
                'atrrib_wind'      => $char->point_wind,
                'atrrib_fire'      => $char->point_fire,
                'atrrib_lightning' => $char->point_lightning,
                'atrrib_water'     => $char->point_water,
                'atrrib_earth'     => $char->point_earth,
                'atrrib_free'      => $char->point_free,
            ],
            'character_slots' => [
                'weapons'     => 100,
                'back_items'  => 100,
                'accessories' => 100,
                'hairstyles'  => 100,
                'clothing'    => 100,
            ],
            'character_sets' => [
                'weapon'          => $char->equipment_weapon ?: 'wpn_01',
                'back_item'       => $char->equipment_back ?: 'back_01',
                'accessory'       => $char->equipment_accessory ?: 'accessory_01',
                'hairstyle'       => $hairstyle,
                'clothing'        => $char->equipment_clothing ?: 'set_01' . $genderSuffix,
                'skills'          => $equippedSkills,
                'senjutsu_skills' => $char->senjutsu_equipped_skills ?: '',
                'hair_color'      => $char->hair_color ?? '0|0',
                'skin_color'      => $char->skin_color ?? 'null|null',
                'face'            => 'face_01' . $genderSuffix,
                'pet'             => $petEquippedId,
                'anims'           => [],
            ],
            'character_inventory' => [
                'char_talent_skills'   => $talentSkillsStr,
                'char_senjutsu_skills' => $char->senjutsu_skills ?: "",
            ],
            'features'     => ['pvp'],
            'recruiters'   => [],
            'recruit_data' => [],
            'pet_data'     => $petData,
            'clan'         => null,
        ];
    }
}