<?php

namespace App\Services\Amf\DailyRewardService;

use App\Models\Character;
use App\Services\Amf\Concerns\ValidatesSession;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class XpService
{
    use ValidatesSession;

    /**
     * claimDailyXP
     * Params: [charId, sessionKey]
     */
    public function claimDailyXP($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF DailyReward.claimDailyXP: Char $charId");

        $char = Character::find($charId);
        if (!$char) {
            return ['status' => 0, 'error' => 'Character not found'];
        }

        // Cek sudah claim hari ini
        $today = Carbon::today();
        if ($char->daily_xp_claimed_at &&
            Carbon::parse($char->daily_xp_claimed_at)->gte($today)) {
            return ['status' => 2, 'result' => 'Already claimed today!'];
        }

        /*
        |--------------------------------------------------------------------------
        | Slightly OP Settings (But Still Safe)
        |--------------------------------------------------------------------------
        */

        $doubleXpChance = 20; // 20% chance
        $doubleXpMin = 60;    // 60%
        $doubleXpMax = 90;    // 90%

        $xpMinMultiplier = 40; // level × 40
        $xpMaxMultiplier = 75; // level × 75

        $roll = mt_rand(1, 100);

        $xpReward = 0;
        $doubleXpDuration = 0;
        $levelUp = false;
        $bonusRate = 0;

        if ($roll <= $doubleXpChance) {

            /*
            |--------------------------------------------------------------------------
            | DOUBLE XP MODE
            |--------------------------------------------------------------------------
            */

            $doubleXpDuration = 3600; // 1 hour
            $bonusRate = mt_rand($doubleXpMin, $doubleXpMax);

            $char->double_xp_expire_at = Carbon::now()->addSeconds($doubleXpDuration);
            $char->xp_bonus_rate = $bonusRate;

        } else {

            /*
            |--------------------------------------------------------------------------
            | NORMAL XP REWARD
            |--------------------------------------------------------------------------
            */

            $multiplier = mt_rand($xpMinMultiplier, $xpMaxMultiplier);
            $xpReward = $char->level * $multiplier;

            if ($char->isLevelCapped()) {
                $xpReward = 0;
            }

            $levelUp = $char->addXp($xpReward);

            // Reset buff jika dapat flat XP
            $char->xp_bonus_rate = 0;
            $char->double_xp_expire_at = null;
        }

        $char->daily_xp_claimed_at = now();
        $char->save();

        return [
            'status' => 1,
            'xp' => $char->xp,
            'reward' => $xpReward,
            'level_up' => $levelUp,
            'double_xp' => $doubleXpDuration > 0,
            'timer' => $doubleXpDuration,
            'bonus_rate' => $bonusRate
        ];
    }

    /**
     * claimDoubleXP
     */
    public function claimDoubleXP($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF DailyReward.claimDoubleXP: Char $charId");

        $char = Character::find($charId);
        if (!$char) {
            return ['status' => 0, 'error' => 'Character not found'];
        }

        $today = Carbon::today();
        if ($char->daily_xp_claimed_at &&
            Carbon::parse($char->daily_xp_claimed_at)->gte($today)) {
            return ['status' => 2, 'result' => 'Already claimed today!'];
        }

        $duration = 3600;
        $bonusRate = 75; // Mid-high fixed buff

        $char->double_xp_expire_at = Carbon::now()->addSeconds($duration);
        $char->xp_bonus_rate = $bonusRate;
        $char->daily_xp_claimed_at = now();
        $char->save();

        return [
            'status' => 1,
            'timer' => $duration,
            'bonus_rate' => $bonusRate
        ];
    }
}