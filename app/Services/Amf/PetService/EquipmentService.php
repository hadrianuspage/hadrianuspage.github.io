<?php

namespace App\Services\Amf\PetService;

use App\Models\Character;
use App\Models\CharacterPet;
use App\Models\Pet;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class EquipmentService
{
    use ValidatesSession;

    /**
     * Custom skills calculation berdasarkan pet_id dan level
     */
    private function calculateCustomSkills($petId, $level): string
    {
        $cleanPetId = str_replace('pet_', '', $petId);
        
        // ✅ CUSTOM LOGIC DI SINI - Sesuai keinginan
        // Contoh: semua pet dapat skills berdasarkan level intervals
        
        if ($level >= 1) {
            return "1,1,1,1,1,1"; // Level 50+ = 6 skills
        } elseif ($level >= 1) {
            return "1,1,1,1,1,0"; // Level 40+ = 5 skills
        } elseif ($level >= 1) {
            return "1,1,1,1,0,0"; // Level 30+ = 4 skills
        } elseif ($level >= 1) {
            return "1,1,1,0,0,0"; // Level 20+ = 3 skills
        } elseif ($level >= 1) {
            return "1,1,0,0,0,0"; // Level 10+ = 2 skills
        } else {
            return "1,0,0,0,0,0"; // Level 1-9 = 1 skill
        }
        
        // Atau kamu bisa buat logic lain:
        /*
        // Berdasarkan nama pet
        if (str_contains($cleanPetId, 'dragon')) {
            return $level >= 30 ? "1,1,1,1,1,0" : "1,1,0,0,0,0";
        }
        
        // Berdasarkan ID ranges
        if ($petInstanceId % 2 == 0) {
            return "1,1,1,0,0,0"; // Even ID = 3 skills
        }
        
        // Random skills
        $randomSkills = rand(2, 5);
        $skills = array_fill(0, $randomSkills, 1);
        $skills = array_pad($skills, 6, 0);
        return implode(',', $skills);
        */
    }

    public function equipPet($params)
    {
        $guard = $this->guardCharacterSessionFromParams($params);
        if ($guard) {
            return $guard;
        }

        $charId = $params[0];
        $sessionKey = $params[1];
        $petId = $params[2];

        Log::info("AMF PetService.equipPet: Char $charId Pet Instance $petId");

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        if ($char->rank == 1) {
            return ['status' => 2, 'result' => 'You must be Chunin or higher to use pets!'];
        }

        $pet = CharacterPet::where('character_id', $charId)
            ->where('id', $petId)
            ->first();
        if (!$pet) return ['status' => 0, 'error' => 'Pet not found in your inventory'];

        // Update equipped pet
        $char->update(['equipment_pet' => $pet->id]);

        // ✅ CUSTOM SKILLS CALCULATION - Langsung di sini
        $petSkillsString = $this->calculateCustomSkills($pet->pet_id, (int)$pet->level);
        
        // Fallback ke Pet model jika perlu
        if (!$petSkillsString) {
            $petSkillsString = Pet::calculateSkillsForPet($pet->pet_id, (int)$pet->level);
        }
        
        $petInfo = Pet::getPetInfo($pet->pet_id);

        // Get SWF info
        $cleanPetId = str_replace('pet_', '', $pet->pet_id);
        $petConfig = Pet::where('pet_id', $cleanPetId)->first();
        $petSwf = $petConfig && $petConfig->swf ? $petConfig->swf : $pet->pet_id;

        Log::info("AMF PetService.equipPet Success", [
            'char_id' => $charId,
            'pet_instance_id' => $pet->id,
            'pet_type_id_raw' => $pet->pet_id,
            'pet_type_id_clean' => $cleanPetId,
            'pet_level' => $pet->level,
            'pet_config_found' => $petConfig ? 'YES' : 'NO',
            'custom_skills_string' => $petSkillsString,
            'pet_swf' => $petSwf,
        ]);

        return [
            'status' => 1,
            'pet_id' => $pet->id,
            'pet_type_id' => $pet->pet_id,
            'pet_swf' => $petSwf,
            'pet_name' => $pet->name ?: ($petConfig->name ?? 'Pet'),
            'pet_level' => $pet->level,
            'pet_xp' => $pet->xp,
            'pet_skills' => $petSkillsString, // ✅ Custom calculation
            'pet_mp' => $pet->mp ?? 100,
        ];
    }

    public function unequipPet($params)
    {
        $guard = $this->guardCharacterSessionFromParams($params);
        if ($guard) {
            return $guard;
        }

        $charId = $params[0];
        Log::info("AMF PetService.unequipPet: Char $charId");

        $char = Character::find($charId);
        if ($char) {
            $char->update(['equipment_pet' => null]);
        }

        return ['status' => 1];
    }

    public function getPets($params)
    {
        $guard = $this->guardCharacterSessionFromParams($params);
        if ($guard) {
            return $guard;
        }

        $charId = $params[0];
        Log::info("AMF PetService.getPets: Char $charId");

        $pets = CharacterPet::where('character_id', $charId)->get();
        $petList = [];

        foreach ($pets as $pet) {
            // ✅ Custom skills calculation
            $skillsString = $this->calculateCustomSkills($pet->pet_id, (int)$pet->level);
            
            // Fallback
            if (!$skillsString) {
                $skillsString = Pet::calculateSkillsForPet($pet->pet_id, (int)$pet->level);
            }
            
            $petInfo = Pet::getPetInfo($pet->pet_id);

            $cleanPetId = str_replace('pet_', '', $pet->pet_id);
            $petConfig = Pet::where('pet_id', $cleanPetId)->first();

            $petList[] = [
                'id' => $pet->id,
                'pet_id' => $pet->pet_id,
                'pet_name' => $pet->name ?: ($petConfig->name ?? 'Pet'),
                'pet_level' => $pet->level,
                'pet_xp' => $pet->xp,
                'pet_mp' => $pet->mp ?? 100,
                'pet_hp' => $pet->hp ?? 100,
                'pet_skills' => $skillsString, // ✅ Custom calculation
                'total_skills' => substr_count($skillsString, '1'), // Hitung 1s
                'unlock_levels' => 'custom_logic',
                'pet_swf' => $petConfig && $petConfig->swf ? $petConfig->swf : $pet->pet_id,
            ];
        }

        return [
            'status' => 1,
            'pets' => $petList
        ];
    }
}