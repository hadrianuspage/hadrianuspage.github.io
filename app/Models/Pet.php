<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Log;

class Pet extends Model
{
    use HasFactory;

    protected $fillable = [
        'pet_id',
        'name',
        'swf',
        'price_gold',
        'price_tokens',
        'premium',
        'skills',
        'icon',
    ];

    protected $casts = [
        'premium' => 'boolean',
        'skills'  => 'array',
    ];

    /**
     * Calculate skills string dari config DB dengan format 6 digit fixed
     */
    public function calculateSkillsString($level): string
    {
        if (empty($this->skills)) {
            return '1,0,0,0,0,0'; // Default: 1 skill terbuka
        }

        // Hitung berapa skill yang terbuka
        $unlockedCount = 0;
        foreach ($this->skills as $skill) {
            $reqLevel = $skill['level'] ?? 1;
            if ($level >= $reqLevel) {
                $unlockedCount++;
            }
        }
        
        // Format 6 digit fixed
        $skillsArray = [0, 0, 0, 0, 0, 0];
        for ($i = 0; $i < $unlockedCount; $i++) {
            $skillsArray[$i] = 1;
        }

        return implode(',', $skillsArray);
    }

    /**
     * Simple method - hanya cek DB, jika tidak ada return default
     */
    public static function calculateSkillsForPet($petId, $level): string
    {
        // Hapus prefix jika ada
        $cleanPetId = str_replace('pet_', '', $petId);
        
        // Coba cari config di DB
        $petConfig = self::where('pet_id', $cleanPetId)->first();
        if ($petConfig && !empty($petConfig->skills)) {
            Log::info("Pet skills from database config", [
                'pet_id' => $cleanPetId,
                'level' => $level,
                'skills_config' => $petConfig->skills
            ]);
            return $petConfig->calculateSkillsString($level);
        }

        // Default fallback - 3 skills sederhana
        $defaultUnlockLevels = [1, 15, 30];
        $unlockedCount = 0;
        
        foreach ($defaultUnlockLevels as $requiredLevel) {
            if ($level >= $requiredLevel) {
                $unlockedCount++;
            } else {
                break;
            }
        }

        // Format 6 digit fixed
        $skillsArray = [0, 0, 0, 0, 0, 0];
        for ($i = 0; $i < $unlockedCount; $i++) {
            $skillsArray[$i] = 1;
        }

        Log::info("Pet skills default fallback", [
            'pet_id' => $cleanPetId,
            'level' => $level,
            'unlocked_count' => $unlockedCount,
            'result' => implode(',', $skillsArray)
        ]);

        return implode(',', $skillsArray);
    }

    /**
     * Simple info method
     */
    public static function getPetInfo($petId): array
    {
        $cleanPetId = str_replace('pet_', '', $petId);
        
        // Cek DB config
        $petConfig = self::where('pet_id', $cleanPetId)->first();
        if ($petConfig && !empty($petConfig->skills)) {
            return [
                'pet_id' => $cleanPetId,
                'total_skills' => count($petConfig->skills),
                'unlock_levels' => array_column($petConfig->skills, 'level'),
                'detection_method' => 'database_config'
            ];
        }

        // Default info
        return [
            'pet_id' => $cleanPetId,
            'total_skills' => 3,
            'unlock_levels' => [1, 15, 30],
            'detection_method' => 'default_fallback'
        ];
    }

    /**
     * Get total skills count
     */
    public function getTotalSkills(): int
    {
        if (!empty($this->skills)) {
            return count($this->skills);
        }
        
        return 3; // Default
    }
}

