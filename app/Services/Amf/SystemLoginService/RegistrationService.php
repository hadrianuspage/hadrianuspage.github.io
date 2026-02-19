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
    const MAX_REGISTRATIONS_PER_PERIOD = 3;
    const COOLDOWN_MINUTES = 5;
    
    /**
     * registerUser
     */
    public function registerUser($username, $email, $password, $serverString)
    {
        Log::info("AMF Register Attempt: $username ($email)");

        // Get IP address
        $ipAddress = Request::ip();
        $cacheKey = "registration_count_" . md5($ipAddress);
        
        // Check registration limit (3 accounts per 5 minutes)
        $registrationData = Cache::get($cacheKey, [
            'count' => 0,
            'first_registration' => null,
            'registrations' => []
        ]);
        
        $now = Carbon::now();
        
        // Clean expired registrations (older than 5 minutes)
        $validRegistrations = collect($registrationData['registrations'])
            ->filter(function ($timestamp) use ($now) {
                return $now->diffInMinutes(Carbon::parse($timestamp)) < self::COOLDOWN_MINUTES;
            })
            ->values()
            ->toArray();
        
        $currentCount = count($validRegistrations);
        
        // Check if limit exceeded
        if ($currentCount >= self::MAX_REGISTRATIONS_PER_PERIOD) {
            $oldestRegistration = Carbon::parse($validRegistrations[0]);
            $cooldownEnd = $oldestRegistration->copy()->addMinutes(self::COOLDOWN_MINUTES);
            $remainingTime = $now->diffInSeconds($cooldownEnd);
            $minutes = floor($remainingTime / 60);
            $seconds = $remainingTime % 60;
            
            $timeFormatted = sprintf("%d:%02d", $minutes, $seconds);
            
            Log::warning("Registration limit reached for IP: $ipAddress ({$currentCount}/{" . self::MAX_REGISTRATIONS_PER_PERIOD . "})");
            
            return [
                'status' => 2, 
                'result' => "Registration limit reached! Please wait {$timeFormatted} to register again",
                'cooldown_remaining' => $remainingTime,
                'cooldown_end' => $cooldownEnd->toIso8601String(),
                'registrations_used' => $currentCount,
                'registrations_limit' => self::MAX_REGISTRATIONS_PER_PERIOD
            ];
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
                'tokens' => 1500, // Bonus tokens 1500
            ]);

            Log::info("User created: {$user->id} with 1500 tokens");

            // Update registration count and timestamps
            $validRegistrations[] = $now->toIso8601String();
            
            $newRegistrationData = [
                'count' => count($validRegistrations),
                'first_registration' => $validRegistrations[0],
                'registrations' => $validRegistrations
            ];
            
            // Cache until the oldest registration expires
            $oldestRegistration = Carbon::parse($validRegistrations[0]);
            $cacheExpiry = $oldestRegistration->copy()->addMinutes(self::COOLDOWN_MINUTES);
            
            Cache::put($cacheKey, $newRegistrationData, $cacheExpiry);
            
            Log::info("Registration count updated for IP $ipAddress: {$newRegistrationData['count']}/" . self::MAX_REGISTRATIONS_PER_PERIOD);

            // Calculate remaining registrations
            $remainingRegistrations = self::MAX_REGISTRATIONS_PER_PERIOD - count($validRegistrations);
            
            return [
                'status' => 1, 
                'result' => 'Registered Successfully! You received 1500 tokens as welcome bonus!',
                'registrations_used' => count($validRegistrations),
                'registrations_remaining' => $remainingRegistrations,
                'registrations_limit' => self::MAX_REGISTRATIONS_PER_PERIOD,
                'reset_time' => $cacheExpiry->toIso8601String()
            ];

        } catch (\Exception $e) {
            Log::error("Registration Error: " . $e->getMessage());
            return ['status' => 0, 'error' => 'Internal Server Error'];
        }
    }

    /**
     * Check registration limit status
     * For client to check remaining registrations without attempting registration
     */
    public function checkRegistrationStatus($ipAddress = null)
    {
        $ipAddress = $ipAddress ?: Request::ip();
        $cacheKey = "registration_count_" . md5($ipAddress);
        
        $registrationData = Cache::get($cacheKey, [
            'count' => 0,
            'first_registration' => null,
            'registrations' => []
        ]);
        
        $now = Carbon::now();
        
        // Clean expired registrations
        $validRegistrations = collect($registrationData['registrations'])
            ->filter(function ($timestamp) use ($now) {
                return $now->diffInMinutes(Carbon::parse($timestamp)) < self::COOLDOWN_MINUTES;
            })
            ->values()
            ->toArray();
        
        $currentCount = count($validRegistrations);
        $remainingRegistrations = self::MAX_REGISTRATIONS_PER_PERIOD - $currentCount;
        
        // If no valid registrations, can register
        if ($currentCount === 0) {
            return [
                'status' => 1,
                'can_register' => true,
                'registrations_used' => 0,
                'registrations_remaining' => self::MAX_REGISTRATIONS_PER_PERIOD,
                'registrations_limit' => self::MAX_REGISTRATIONS_PER_PERIOD
            ];
        }
        
        // Update cache if we cleaned some registrations
        if (count($validRegistrations) !== count($registrationData['registrations'])) {
            if (count($validRegistrations) > 0) {
                $newRegistrationData = [
                    'count' => count($validRegistrations),
                    'first_registration' => $validRegistrations[0],
                    'registrations' => $validRegistrations
                ];
                
                $oldestRegistration = Carbon::parse($validRegistrations[0]);
                $cacheExpiry = $oldestRegistration->copy()->addMinutes(self::COOLDOWN_MINUTES);
                Cache::put($cacheKey, $newRegistrationData, $cacheExpiry);
            } else {
                Cache::forget($cacheKey);
            }
        }
        
        // Check if limit reached
        if ($currentCount >= self::MAX_REGISTRATIONS_PER_PERIOD) {
            $oldestRegistration = Carbon::parse($validRegistrations[0]);
            $resetTime = $oldestRegistration->copy()->addMinutes(self::COOLDOWN_MINUTES);
            $remainingTime = $now->diffInSeconds($resetTime);
            $minutes = floor($remainingTime / 60);
            $seconds = $remainingTime % 60;
            
            $timeFormatted = sprintf("%d:%02d", $minutes, $seconds);

            return [
                'status' => 1,
                'can_register' => false,
                'limit_reached' => true,
                'registrations_used' => $currentCount,
                'registrations_remaining' => 0,
                'registrations_limit' => self::MAX_REGISTRATIONS_PER_PERIOD,
                'remaining_seconds' => $remainingTime,
                'remaining_time' => $timeFormatted,
                'reset_time' => $resetTime->toIso8601String()
            ];
        }

        return [
            'status' => 1,
            'can_register' => true,
            'limit_reached' => false,
            'registrations_used' => $currentCount,
            'registrations_remaining' => $remainingRegistrations,
            'registrations_limit' => self::MAX_REGISTRATIONS_PER_PERIOD
        ];
    }
    
    /**
     * Legacy method untuk backward compatibility
     */
    public function checkCooldownStatus($ipAddress = null)
    {
        return $this->checkRegistrationStatus($ipAddress);
    }
}

