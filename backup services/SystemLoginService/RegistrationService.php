<?php

namespace App\Services\Amf\SystemLoginService;

use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Request;
use Carbon\Carbon;

class RegistrationService
{
    /**
     * registerUser
     */
    public function registerUser($username, $email, $password, $serverString)
    {
        Log::info("AMF Register Attempt: $username ($email)");

        // Get IP address
        $ipAddress = Request::ip();
        $cacheKey = "registration_cooldown_" . md5($ipAddress);
        
        // Check registration cooldown (5 minutes)
        $lastRegistration = Cache::get($cacheKey);
        
        if ($lastRegistration) {
            $cooldownEnd = Carbon::parse($lastRegistration)->addMinutes(5);
            $now = Carbon::now();
            
            if ($now->lt($cooldownEnd)) {
                $remainingTime = $now->diffInSeconds($cooldownEnd);
                $minutes = floor($remainingTime / 60);
                $seconds = $remainingTime % 60;
                
                // Fix: Use sprintf for proper formatting
                $timeFormatted = sprintf("%d:%02d", $minutes, $seconds);
                
                Log::warning("Registration cooldown active for IP: $ipAddress");
                return [
                    'status' => 2, 
                    'result' => "Account creation is on cooldown! Wait {$timeFormatted} minutes later",
                    'cooldown_remaining' => $remainingTime, // For client countdown
                    'cooldown_end' => $cooldownEnd->toIso8601String() // ISO format for client
                ];
            }
        }

        // Validate username/email
        if (User::where('username', $username)->exists()) {
            return ['status' => 2, 'result' => 'Username already exists!'];
        }

        if (User::where('email', $email)->exists()) {
            return ['status' => 2, 'result' => 'Email already exists!'];
        }

        try {
            // Create user with bonus tokens
            $user = User::create([
                'username' => $username,
                'email' => $email,
                'password' => Hash::make($password),
                'name' => $username,
                'tokens' => 1500, // Bonus tokens_1500
            ]);

            Log::info("User created: {$user->id} with 1500 tokens");

            // Set cooldown for 5 minutes from now
            $cooldownStart = Carbon::now();
            Cache::put($cacheKey, $cooldownStart->toIso8601String(), $cooldownStart->copy()->addMinutes(5));
            
            Log::info("Registration cooldown set for IP $ipAddress until: " . $cooldownStart->copy()->addMinutes(5)->format('H:i:s'));

            return [
                'status' => 1, 
                'result' => 'Registered Successfully! You received 1500 tokens as welcome bonus!',
                'cooldown_set' => true,
                'next_registration_at' => $cooldownStart->copy()->addMinutes(5)->toIso8601String()
            ];

        } catch (\Exception $e) {
            Log::error("Registration Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Internal Server Error'];
        }
    }

    /**
     * Check registration cooldown status
     * For client to check remaining time without attempting registration
     */
    public function checkCooldownStatus($ipAddress = null)
    {
        $ipAddress = $ipAddress ?: Request::ip();
        $cacheKey = "registration_cooldown_" . md5($ipAddress);
        
        $lastRegistration = Cache::get($cacheKey);
        
        if (!$lastRegistration) {
            return [
                'status' => 1,
                'cooldown_active' => false,
                'can_register' => true
            ];
        }

        $cooldownEnd = Carbon::parse($lastRegistration)->addMinutes(5);
        $now = Carbon::now();
        
        if ($now->gte($cooldownEnd)) {
            // Cooldown expired, remove cache
            Cache::forget($cacheKey);
            return [
                'status' => 1,
                'cooldown_active' => false,
                'can_register' => true
            ];
        }

        $remainingTime = $now->diffInSeconds($cooldownEnd);
        $minutes = floor($remainingTime / 60);
        $seconds = $remainingTime % 60;
        
        // Fix: Use sprintf for proper formatting
        $timeFormatted = sprintf("%d:%02d", $minutes, $seconds);

        return [
            'status' => 1,
            'cooldown_active' => true,
            'can_register' => false,
            'remaining_seconds' => $remainingTime,
            'remaining_time' => $timeFormatted,
            'cooldown_end' => $cooldownEnd->toIso8601String()
        ];
    }
}

