<?php

namespace App\Services\Amf\CharacterService;

use App\Models\Character;
use App\Models\CharacterRecruit;
use App\Models\Npc;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class MissionService
{
    use ValidatesSession;

    /**
     * getMissionRoomData
     */
    public function getMissionRoomData($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF Get Mission Room Data: Char $charId");

        $recruits = CharacterRecruit::where('character_id', $charId)->get();
        $recruitData = [];

        foreach ($recruits as $r) {
            $recruitId = $r->recruit_id;
            
            Log::info("DEBUG: Processing recruit_id: $recruitId");

            // SKIP character recruits untuk testing
            if (str_starts_with($recruitId, 'char_')) {
                Log::info("DEBUG: Skipping character recruit: $recruitId");
                continue; // Skip character recruits
            }

            // Only process NPC recruits
            $isNpc = false;
            if (str_starts_with($recruitId, 'npc_')) {
                $isNpc = true;
            } else {
                if (Npc::where('npc_id', $recruitId)->exists()) {
                    $isNpc = true;
                } elseif (Npc::where('npc_id', 'npc_' . $recruitId)->exists()) {
                    $isNpc = true;
                    $recruitId = 'npc_' . $recruitId;
                }
            }

            if ($isNpc) {
                $recruitData[] = [
                    'type' => 'npc',
                    'id' => ['recruiter_id' => $recruitId]
                ];
                Log::info("DEBUG: Added NPC recruit: $recruitId");
            }
        }

        Log::info("DEBUG: Final recruit data: " . json_encode($recruitData));

        return [
            'status' => 1,
            'error' => 0,
            'recruit' => $recruitData,
            'daily' => []
        ];
    }
}