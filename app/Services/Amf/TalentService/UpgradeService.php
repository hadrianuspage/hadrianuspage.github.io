<?php

namespace App\Services\Amf\TalentService;

use App\Models\Character;
use App\Models\CharacterTalent;
use App\Models\GameConfig;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class UpgradeService
{
    use ValidatesSession;

    public function upgradeSkill($charIdOrParams, $sessionKey = null, $baseSkillId = null, $isMax = false)
    {
        if (is_array($charIdOrParams)) {
            $charId      = $charIdOrParams[0];
            $sessionKey  = $charIdOrParams[1] ?? null;
            $baseSkillId = $charIdOrParams[2] ?? null;
            $isMax       = isset($charIdOrParams[3]) ? (bool)$charIdOrParams[3] : false;
        } else {
            $charId = $charIdOrParams;
        }

        $charId      = (int) $charId;
        $baseSkillId = trim((string) $baseSkillId);

        $guard = $this->guardCharacterSession($charId, $sessionKey);
        if ($guard) return $guard;

        Log::info("AMF Talent.upgradeSkill START: char={$charId} skill=[{$baseSkillId}] isMax=" . ($isMax ? 'true' : 'false'));

        if ($baseSkillId === '' || $baseSkillId === 'null') {
            Log::error("AMF Talent.upgradeSkill: baseSkillId kosong atau null!");
            return ['status' => 0, 'error' => 'Invalid skill ID'];
        }

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        $tableName = (new CharacterTalent)->getTable();

        $existing = DB::table($tableName)
            ->where('character_id', $charId)
            ->where('skill_id', $baseSkillId)
            ->first();

        $currentLevel = $existing ? (int) $existing->level : 0;

        Log::info("AMF Talent.upgradeSkill: existing=" . json_encode($existing) . " currentLevel={$currentLevel}");

        if ($currentLevel >= 10) {
            return ['status' => 2, 'result' => 'Already at maximum level!'];
        }

        $totalSpentTp = 0;
        $targetLevel  = $currentLevel;

        if ($isMax) {
            $tempLevel = $currentLevel + 1;
            while ($tempLevel <= 10) {
                $cost = $this->getTpCost($tempLevel);
                if (($char->tp - $totalSpentTp) >= $cost) {
                    $totalSpentTp += $cost;
                    $targetLevel = $tempLevel;
                    $tempLevel++;
                } else {
                    break;
                }
            }
            if ($targetLevel <= $currentLevel) {
                return ['status' => 2, 'result' => 'Not enough TP to upgrade even one level!'];
            }
        } else {
            $targetLevel  = $currentLevel + 1;
            $totalSpentTp = $this->getTpCost($targetLevel);
            if ($char->tp < $totalSpentTp) {
                return ['status' => 2, 'result' => 'Not enough TP!'];
            }
        }

        Log::info("AMF Talent.upgradeSkill: UPGRADING {$currentLevel} → {$targetLevel}, cost={$totalSpentTp}, tp_before={$char->tp}");

        // Kurangi TP
        $char->tp -= $totalSpentTp;
        $char->save();

        // INSERT atau UPDATE
        if ($existing) {
            $affected = DB::table($tableName)
                ->where('character_id', $charId)
                ->where('skill_id', $baseSkillId)
                ->update(['level' => $targetLevel]);

            Log::info("AMF Talent.upgradeSkill: UPDATE affected rows={$affected}");
        } else {
            DB::table($tableName)->insert([
                'character_id' => $charId,
                'skill_id'     => $baseSkillId,
                'level'        => $targetLevel,
            ]);
            Log::info("AMF Talent.upgradeSkill: INSERT new record");
        }

        // Verifikasi tersimpan
        $verify = DB::table($tableName)
            ->where('character_id', $charId)
            ->where('skill_id', $baseSkillId)
            ->value('level');

        Log::info("AMF Talent.upgradeSkill: VERIFY saved level={$verify} (expected={$targetLevel})");

        if ((int)$verify !== $targetLevel) {
            Log::error("AMF Talent.upgradeSkill: MISMATCH! DB={$verify} expected={$targetLevel}");
        }

        // Sync talent string di kolom character
        TalentStringService::syncTalentString($charId);

        // =============================================
        // Fetch semua talent terbaru untuk dikirim ke Flash client
        // supaya client tidak perlu re-call getTalentSkills
        // =============================================
        $allTalents = DB::table($tableName)
            ->where('character_id', $charId)
            ->get();

        $talentData = [];
        foreach ($allTalents as $t) {
            $talentData[] = [
                'item_id'    => $t->skill_id,
                'item_level' => (int) $t->level,
            ];
        }

        Log::info("AMF Talent.upgradeSkill: Returning talent_data=" . json_encode($talentData));

        return [
            'status'      => 1,
            'current_tp'  => (int) $char->tp,
            'new_level'   => (int) $targetLevel,
            'result'      => 'Talent upgraded successfully!',
            'talent_data' => $talentData,
        ];
    }

    private function getTpCost($level)
    {
        $costs = GameConfig::get('talent_tp_cost');
        if (!$costs || !is_array($costs)) {
            $costs = [
                1 => 5,   2 => 10,  3 => 25,  4 => 50,   5 => 100,
                6 => 200, 7 => 300, 8 => 450, 9 => 600, 10 => 800
            ];
        }
        return $costs[$level] ?? 999999;
    }
}