<?php

namespace App\Services\Amf\SystemLoginService;

use App\Models\User;
use Carbon\Carbon;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class LoginService
{
    /**
     * loginUser dengan login logging
     */
    public function loginUser($username, $encryptedPassword, $char_, $bl, $bt, $char__, $item, $seed, $passLen)
    {
        Log::info("LOGIN_ATTEMPT - Username: $username");

        // ========== 1. VERIFY USER EXISTS ==========
        $user = User::where('username', $username)->first();

        if (!$user) {
            Log::warning("LOGIN_FAILED - Username: $username");
            
            // LOG KE DATABASE - LOGIN GAGAL
            $this->logLogin(null, false, 'User not found');
            
            return ['status' => 2, 'error' => 'Invalid credentials'];
        }

        // ========== 2. VERIFY PASSWORD ==========
        $decryptedPassword = $this->decryptPassword($encryptedPassword, $char__, $char_);

        if (!$decryptedPassword || !Hash::check($decryptedPassword, $user->password)) {
            Log::warning("LOGIN_FAILED - UserId: {$user->id} - Invalid password");
            
            // LOG KE DATABASE - LOGIN GAGAL
            $this->logLogin($user->id, false, 'Invalid password');
            
            return ['status' => 2, 'error' => 'Invalid credentials'];
        }

        // ========== 3. CREATE SESSION ==========
        $sessionKey = Str::random(32);
        $user->session_key = $sessionKey;
        $user->save();

        Log::info("LOGIN_SUCCESS - UserId: {$user->id}");
        
        // LOG KE DATABASE - LOGIN SUKSES
        $this->logLogin($user->id, true, 'Login successful');

        return [
            'status' => 1,
            'error' => 0,
            'uid' => $user->id,
            'sessionkey' => $sessionKey,
            '__' => $char__,
            'events' => $this->getEvents(),
            'clan_season' => 1,
            'crew_season' => 1,
            'sw_season' => 1,
            'banners' => [],
            'system_time' => base64_encode(time())
        ];
    }

    /**
     * Log login attempt ke database
     */
    private function logLogin(?int $userId, bool $success, string $reason): void
    {
        try {
            DB::table('login_logs')->insert([
                'user_id' => $userId,
                'ip_address' => request()->ip(),
                'user_agent' => substr(request()->header('User-Agent', 'N/A'), 0, 255),
                'success' => $success,
                'reason' => $reason,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        } catch (\Exception $e) {
            Log::error("Failed to log login: " . $e->getMessage());
        }
    }

    private function getEvents(): array
    {
        return [
            'welcome_bonus',
            'mysterious-market',
            'chunin_package',
            'special-deals',
            'monster_hunter_2023',
            'dragon_hunt_2024',
            'justice-badge2024',
            'giveaway-center',
            'leaderboard',
            'tailedbeast',
            'dailygacha',
            'dragongacha',
            'exoticpackage',
            'confronting-death-2025',
            'thanksgiving2025',
            'elementalars',
            'xmass2025',
        ];
    }

    private function decryptPassword($encryptedBase64, $keyString, $ivString)
    {
        try {
            $key = $keyString;
            $iv = $this->pkcs5Pad($ivString, 16);
            $encryptedData = base64_decode($encryptedBase64);
            return openssl_decrypt($encryptedData, 'aes-128-cbc', $key, OPENSSL_RAW_DATA, $iv);
        } catch (\Exception $e) {
            Log::error("DECRYPTION_ERROR: " . $e->getMessage());
            return false;
        }
    }

    private function pkcs5Pad($text, $blocksize)
    {
        $pad = $blocksize - (strlen($text) % $blocksize);
        return $text . str_repeat(chr($pad), $pad);
    }
}