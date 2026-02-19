<?php

namespace App\Services\Amf\BattleSystemService;

use App\Models\Character;
use App\Models\Enemy;
use App\Services\Amf\SessionValidator;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Str;

class StartService
{
    /**
     * startMission
     */
    public function startMission($charId, $missionId, $enemyId, $enemyStats, $unknown, $hash, $sessionKey)
    {
        Log::info("AMF Start Mission: Char $charId Mission '$missionId'");

        $guard = SessionValidator::validateCharacter((int)$charId, $sessionKey);
        if ($guard) return $guard;

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        // DEBUG: Log exact mission ID yang diterima
        Log::info("DEBUG: Received Mission ID: '" . $missionId . "' (length: " . strlen($missionId) . ")");

        // Validate Mission
        $mission = \App\Models\Mission::where('mission_id', $missionId)->first();

        if (!$mission) {
            // Check for padded/unpadded match
            if (str_starts_with($missionId, 'msn_')) {
                $num = intval(substr($missionId, 4));
                $paddedId = 'msn_' . str_pad($num, 2, '0', STR_PAD_LEFT);
                $mission = \App\Models\Mission::where('mission_id', $paddedId)->first();
                Log::info("DEBUG: Trying padded ID: '$paddedId'");
            }
        }

        if (!$mission) {
            Log::error("Mission data not found for ID: '$missionId'");
            return ['status' => 0, 'error' => 'Mission data not found'];
        }

        // Level Requirement Check
        if ($char->level < $mission->req_lvl) {
            return ['status' => 0, 'error' => 'Level too low'];
        }

        // PERBAIKAN: Deteksi Mission Type dengan Multiple Methods
        $isMissionS = $this->detectMissionType($missionId, $mission);
        
        Log::info("DEBUG: Mission Type Detection Result: '$missionId' -> " . ($isMissionS ? 'SPECIAL (S Grade)' : 'NORMAL (C/B/A Grade)'));

        if ($isMissionS) {
            // MISSION S: Energy System
            Log::info("DEBUG: Applying energy system for Mission S");
            
            $energyResult = $this->checkAndDeductEnergy($charId, $missionId);
            if ($energyResult !== true) {
                return $energyResult; // Return error response
            }
        } else {
            // NORMAL MISSION: Unlimited
            Log::info("DEBUG: Normal mission - no energy check required");
        }

        // Validate Enemy Data (optional validation)
        $missionDef = $this->getMissionDefinition($missionId);
        $validationResult = $this->validateEnemyData($missionDef, $enemyId, $enemyStats, $hash, $unknown);
        
        if ($validationResult !== true && $isMissionS) {
            // Refund energy if validation fails for Mission S
            $this->refundEnergy($charId, 10);
            return $validationResult;
        } else if ($validationResult !== true) {
            return $validationResult;
        }

        $token = Str::random(10);

        Log::info("Mission Started Successfully: $missionId. Rewards: Gold={$mission->gold}, XP={$mission->xp}");

        // Store mission data in cache
        Cache::put("battle_token_$charId", [
            'token' => $token,
            'mission_id' => $mission->mission_id ?? $missionId,
            'reward_xp' => (int)$mission->xp,
            'reward_gold' => (int)$mission->gold,
            'start_time' => now(),
            'is_mission_s' => $isMissionS,
            'energy_cost' => $isMissionS ? 10 : 0
        ], 1800);

        return $token;
    }

    /**
     * Detect if mission is Special (S Grade) or Normal (C/B/A Grade)
     */
    private function detectMissionType(string $missionId, $mission): bool
    {
        Log::info("DEBUG: Detecting mission type for '$missionId'");
        
        // Method 1: Check mission.json definition
        $missionDef = $this->getMissionDefinition($missionId);
        if ($missionDef) {
            $grade = strtolower(trim($missionDef['grade'] ?? ''));
            $category = strtolower(trim($missionDef['category'] ?? ''));
            
            Log::info("DEBUG: Mission def found - Grade: '$grade', Category: '$category'");
            
            if ($grade === 's' || $category === 'special' || $category === 's') {
                Log::info("DEBUG: Mission S detected via mission.json definition");
                return true;
            }
        }
        
        // Method 2: Check database mission table
        if ($mission && isset($mission->category)) {
            $dbCategory = strtolower(trim($mission->category));
            Log::info("DEBUG: DB Category: '$dbCategory'");
            
            if ($dbCategory === 'special' || $dbCategory === 's') {
                Log::info("DEBUG: Mission S detected via database category");
                return true;
            }
        }
        
        // Method 3: Pattern matching on mission ID
        $patterns = [
            '/grade[_\s]*s/i',           // "grade_s", "Grade S"
            '/msn[_\s]*s[_\s]/i',        // "msn_s_", "MSN S "
            '/stage[_\s]*\d+/i',         // "stage_1", "Stage 1"
            '/special/i',                // "special"
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $missionId)) {
                Log::info("DEBUG: Mission S detected via pattern: $pattern");
                return true;
            }
        }
        
        Log::info("DEBUG: Normal mission detected (no S grade indicators found)");
        return false;
    }

    /**
     * Check and deduct energy for Mission S
     */
    private function checkAndDeductEnergy(int $charId, string $missionId): mixed
    {
        $energyCost = 10; // Default cost
        
        // Get mission definition for specific energy cost
        $missionDef = $this->getMissionDefinition($missionId);
        if ($missionDef && isset($missionDef['energy_cost'])) {
            $energyCost = (int)$missionDef['energy_cost'];
        }
        
        $energyKey = "mission_s_energy_$charId";
        $currentEnergy = Cache::get($energyKey);
        
        if ($currentEnergy === null) {
            $currentEnergy = 25; // MAX_ENERGY
            Cache::put($energyKey, $currentEnergy, 86400);
        }
        
        Log::info("DEBUG: Energy check - Current: $currentEnergy, Required: $energyCost");
        
        // Check energy
        if ($currentEnergy < $energyCost) {
            Log::warning("DEBUG: Not enough energy! Current: $currentEnergy, Need: $energyCost");
            return ['status' => 0, 'error' => 'Not enough energy to enter this mission'];
        }

        // Deduct energy
        $newEnergy = $currentEnergy - $energyCost;
        Cache::put($energyKey, $newEnergy, 86400);
        
        Log::info("DEBUG: Energy deducted successfully - Cost: $energyCost, Remaining: $newEnergy");
        return true;
    }

    /**
     * Refund energy (when validation fails)
     */
    private function refundEnergy(int $charId, int $amount): void
    {
        $energyKey = "mission_s_energy_$charId";
        $currentEnergy = Cache::get($energyKey, 0);
        $newEnergy = min(25, $currentEnergy + $amount);
        Cache::put($energyKey, $newEnergy, 86400);
        
        Log::info("DEBUG: Energy refunded - Amount: $amount, New total: $newEnergy");
    }

    /**
     * Validate enemy data (optional, can be skipped)
     */
    private function validateEnemyData(?array $missionDef, string $enemyId, string $enemyStats, string $hash, string $unknown): mixed
    {
        if (!$missionDef) {
            Log::info("DEBUG: No mission definition found, skipping enemy validation");
            return true; // Skip validation if no definition
        }
        
        $expectedEnemies = $missionDef['enemies'] ?? [];
        if (empty($expectedEnemies)) {
            Log::info("DEBUG: No expected enemies defined, skipping enemy validation");
            return true; // Skip validation if no enemies defined
        }
        
        Log::info("DEBUG: Validating enemies - Expected: " . implode(',', $expectedEnemies));
        
        $providedEnemies = array_values(array_filter(explode(',', (string)$enemyId), 'strlen'));
        
        if (count($expectedEnemies) !== count($providedEnemies)) {
            Log::warning("DEBUG: Enemy count mismatch - Expected: " . count($expectedEnemies) . ", Got: " . count($providedEnemies));
            return ['status' => 0, 'error' => 'Invalid enemies'];
        }

        foreach ($expectedEnemies as $index => $expectedId) {
            if (!isset($providedEnemies[$index]) || $providedEnemies[$index] !== $expectedId) {
                Log::warning("DEBUG: Enemy ID mismatch at index $index - Expected: '$expectedId', Got: '" . ($providedEnemies[$index] ?? 'null') . "'");
                return ['status' => 0, 'error' => 'Invalid enemies'];
            }
        }

        // Skip detailed stats validation for now (can be enabled later)
        Log::info("DEBUG: Enemy validation passed");
        return true;
    }

    private function getMissionDefinition(string $missionId): ?array
    {
        $missions = Cache::remember('mission_definitions_map', 3600, function () {
            $path = base_path('public/game_data/mission.json');
            if (!File::exists($path)) {
                Log::warning("DEBUG: mission.json not found at: $path");
                return [];
            }

            $content = File::get($path);
            $list = json_decode($content, true);
            if (!is_array($list)) {
                Log::warning("DEBUG: mission.json is not valid JSON array");
                return [];
            }

            $map = [];
            foreach ($list as $entry) {
                if (!is_array($entry) || !isset($entry['id'])) {
                    continue;
                }

                $id = (string)$entry['id'];
                $map[$id] = $entry;

                // Support multiple ID formats
                if (preg_match('/^msn_0*(\d+)$/', $id, $matches)) {
                    $num = (int)$matches[1];
                    $normalized = 'msn_' . $num;
                    $padded = 'msn_' . str_pad($num, 2, '0', STR_PAD_LEFT);
                    $map[$normalized] = $entry;
                    $map[$padded] = $entry;
                }
            }

            Log::info("DEBUG: Loaded " . count($map) . " mission definitions");
            return $map;
        });

        $result = $missions[$missionId] ?? null;
        Log::info("DEBUG: Mission definition lookup for '$missionId': " . ($result ? 'FOUND' : 'NOT FOUND'));
        
        return $result;
    }

    private function parseEnemyStats(string $enemyStats): array
    {
        $result = [];
        $chunks = array_filter(explode('#', $enemyStats), 'strlen');
        foreach ($chunks as $chunk) {
            $parts = explode('|', $chunk);
            $entry = [];
            foreach ($parts as $part) {
                $kv = explode(':', $part, 2);
                if (count($kv) !== 2) {
                    continue;
                }
                $entry[$kv[0]] = $kv[1];
            }

            if (isset($entry['id'])) {
                $result[$entry['id']] = [
                    'hp' => $entry['hp'] ?? null,
                    'agility' => $entry['agility'] ?? null,
                ];
            }
        }

        return $result;
    }

    private function validateHash(string $hash, string $payload): bool
    {
        $hash = trim($hash);
        if ($hash === '') {
            return true;
        }

        return match (strlen($hash)) {
            32 => hash('md5', $payload) === $hash,
            40 => hash('sha1', $payload) === $hash,
            64 => hash('sha256', $payload) === $hash,
            default => true,
        };
    }
}