<?php

namespace App\Services\Amf\HuntingHouseService;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Services\Amf\Concerns\ValidatesSession;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class DataService
{
    use ValidatesSession;

    /**
     * getData
     * Params: [charId, sessionKey]
     */
    public function getData($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF HuntingHouse.getData: Char $charId");

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error' => 'Character not found'];

        $today = Carbon::today()->toDateString();

        // Handle daily material claim status
        $dailyClaimed = false;
        if ($char->hunting_house_date === $today) {
            $dailyClaimed = true;
        }

        // Kari Badge count
        $material = CharacterItem::where('character_id', $charId)
            ->where('item_id', 'material_509')
            ->value('quantity') ?: 0;

        // Mock Zones and Bosses since they are missing from GameData
        // In a real scenario, these should be in GameConfig
        $zones = [
            [
                'easyBoss' => ['ene_81'],
                'hardBoss' => ['ene_81', 'ene_82']
            ],
            [
                'easyBoss' => ['ene_83'],
                'hardBoss' => ['ene_83', 'ene_84']
            ],
            [
                'easyBoss' => ['ene_85'],
                'hardBoss' => ['ene_85', 'ene_86']
            ],
            [
                'easyBoss' => ['ene_120'],
                'hardBoss' => ['ene_120', 'ene_155']
            ],
            [
                'easyBoss' => ['ene_106'],
                'hardBoss' => ['ene_106', 'ene_101']
            ]
        ];

        $bosses = [
            'ene_81' => ['name' => 'Ginkotsu', 'description' => 'A mechanical terror.', 'rewards' => ['material_501', 'wpn_81']],
            'ene_82' => ['name' => 'Shikigami Yanki', 'description' => 'A paper spirit.', 'rewards' => ['material_502']],
            'ene_83' => ['name' => 'Gedo Sessho Seki', 'description' => 'The killing stone.', 'rewards' => ['material_503']],
            'ene_84' => ['name' => 'Tengu - Fire', 'description' => 'Fire Tengu.', 'rewards' => ['material_504']],
            'ene_85' => ['name' => 'Tengu - Wind', 'description' => 'Wind Tengu.', 'rewards' => ['material_505']],
            'ene_86' => ['name' => 'Byakko', 'description' => 'The White Tiger.', 'rewards' => ['material_506']],
            'ene_120' => ['name' => 'Battle Turtle', 'description' => 'Giant Turtle.', 'rewards' => ['material_507']],
            'ene_155' => ['name' => 'Soul General Mutoh', 'description' => 'Undead General.', 'rewards' => ['material_508']],
            'ene_106' => ['name' => 'Ape King', 'description' => 'King of Apes.', 'rewards' => ['material_509']],
            'ene_101' => ['name' => 'Yamata no Orochi', 'description' => 'Eight-headed serpent.', 'rewards' => ['material_510']]
        ];

        return [
            'status' => 1,
            'material' => (int)$material,
            'daily_claim' => $dailyClaimed,
            'zones' => $zones,
            'bosses' => $bosses
        ];
    }
}
