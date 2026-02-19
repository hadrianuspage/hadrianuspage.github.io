<?php

namespace App\Services\Amf\EudemonGardenService;

use App\Models\Character;
use App\Models\GameConfig;
use App\Services\Amf\Concerns\ValidatesSession;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class DataService
{
    use ValidatesSession;

    /**
     * getData
     * Params: [sessionKey, charId]
     */
    public function getData($sessionKey, $charId)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF EudemonGarden.getData: Char $charId");

        $char = Character::find($charId);
        if (!$char) return ['status' => 0, 'error_code' => 'Character not found'];

        $today = Carbon::today()->toDateString();
        $bosses = GameConfig::get('eudemon')['bosses'] ?? [];
        $bossCount = count($bosses);

        // Reset daily or fix mismatch
        $triesArr = $char->eudemon_garden_tries ? explode(',', $char->eudemon_garden_tries) : [];
        if ($char->eudemon_garden_date !== $today || count($triesArr) !== $bossCount) {
            $char->eudemon_garden_date = $today;
            // Default 3 tries per boss
            $char->eudemon_garden_tries = implode(',', array_fill(0, $bossCount, 3));
            $char->save();
        }

        return [
            'status' => 1,
            'data' => $char->eudemon_garden_tries
        ];
    }
}
