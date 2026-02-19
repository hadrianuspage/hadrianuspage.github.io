<?php

namespace App\Models;

use Carbon\Carbon;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Session;

class CharacterPhantomKyunoki
{
    // HARDCODED CONSTANTS
    private const MAX_ENERGY = 8;
    private const ENERGY_REFILL_MINUTES = 20; // 20 menit per energy
    private const REFILL_PRICE = 50;
    private const SESSION_KEY_PREFIX = 'phantom_kyunoki_';

    /**
     * Get event data for character (dari session)
     */
    public static function getData($characterId)
    {
        $sessionKey = self::SESSION_KEY_PREFIX . $characterId;
        
        if (!Session::has($sessionKey)) {
            $defaultData = [
                'energy' => self::MAX_ENERGY,
                'total_kills' => 0,
                'last_energy_reset' => Carbon::now()->toDateTimeString(),
                'milestone_data' => [
                    ['claimed' => false], // 50 kills
                    ['claimed' => false], // 100 kills  
                    ['claimed' => false], // 200 kills
                    ['claimed' => false]  // 300 kills
                ]
            ];
            
            Session::put($sessionKey, $defaultData);
            Log::info("PhantomKyunoki: Created new session data for char $characterId");
        }
        
        $data = Session::get($sessionKey);
        
        // Convert last_energy_reset back to Carbon if it's a string
        if (is_string($data['last_energy_reset'])) {
            $data['last_energy_reset'] = Carbon::parse($data['last_energy_reset']);
        }
        
        return $data;
    }

    /**
     * Set event data for character
     */
    public static function setData($characterId, $data)
    {
        $sessionKey = self::SESSION_KEY_PREFIX . $characterId;
        
        // Convert Carbon to string for session storage
        if ($data['last_energy_reset'] instanceof Carbon) {
            $data['last_energy_reset'] = $data['last_energy_reset']->toDateTimeString();
        }
        
        Session::put($sessionKey, $data);
        Log::info("PhantomKyunoki: Updated session data for char $characterId - Energy: {$data['energy']}, Kills: {$data['total_kills']}");
    }

    /**
     * Auto refill energy berdasarkan waktu (20 menit per energy)
     */
    public static function autoRefillEnergy($characterId)
    {
        $data = self::getData($characterId);
        
        if ($data['energy'] >= self::MAX_ENERGY) {
            return $data; // Sudah full
        }

        $lastEnergyTime = $data['last_energy_reset'];
        $now = Carbon::now();
        
        // Hitung berapa menit yang sudah lewat
        $minutesPassed = $now->diffInMinutes($lastEnergyTime);
        
        // Setiap 20 menit = 1 energy
        $energyToAdd = floor($minutesPassed / self::ENERGY_REFILL_MINUTES);
        
        if ($energyToAdd > 0) {
            $oldEnergy = $data['energy'];
            $data['energy'] = min(self::MAX_ENERGY, $data['energy'] + $energyToAdd);
            
            // Update waktu dengan sisa menit yang belum cukup untuk 1 energy
            $remainingMinutes = $minutesPassed % self::ENERGY_REFILL_MINUTES;
            $data['last_energy_reset'] = $now->subMinutes($remainingMinutes);
            
            self::setData($characterId, $data);
            
            Log::info("PhantomKyunoki Auto refilled energy: {$oldEnergy} -> {$data['energy']} (+{$energyToAdd})");
        }
        
        return $data;
    }

    /**
     * Increment kill count
     */
    public static function incrementKills($characterId)
    {
        $data = self::getData($characterId);
        $oldKills = $data['total_kills'];
        $data['total_kills']++;
        self::setData($characterId, $data);
        
        Log::info("PhantomKyunoki Kills incremented: {$oldKills} -> {$data['total_kills']}");
        return $data;
    }

    /**
     * Use energy
     */
    public static function useEnergy($characterId, $amount = 1)
    {
        $data = self::getData($characterId);
        
        if ($data['energy'] >= $amount) {
            $oldEnergy = $data['energy'];
            $data['energy'] -= $amount;
            self::setData($characterId, $data);
            
            Log::info("PhantomKyunoki Energy used: -{$amount}, {$oldEnergy} -> {$data['energy']}");
            return true;
        }
        
        Log::warning("PhantomKyunoki Energy insufficient: {$data['energy']} < $amount");
        return false;
    }

    /**
     * Refill energy dengan token (langsung full)
     */
    public static function refillEnergyWithToken($characterId)
    {
        $data = self::getData($characterId);
        $oldEnergy = $data['energy'];
        $data['energy'] = self::MAX_ENERGY;
        $data['last_energy_reset'] = Carbon::now();
        self::setData($characterId, $data);
        
        Log::info("PhantomKyunoki Energy refilled with token: {$oldEnergy} -> " . self::MAX_ENERGY);
        return $data;
    }

    /**
     * Get milestone data
     */
    public static function getMilestoneData($characterId)
    {
        $data = self::getData($characterId);
        return $data['milestone_data'];
    }

    /**
     * Set milestone data
     */
    public static function setMilestoneData($characterId, $milestoneData)
    {
        $data = self::getData($characterId);
        $data['milestone_data'] = $milestoneData;
        self::setData($characterId, $data);
        return $data;
    }

    /**
     * Get waktu kapan energy berikutnya akan di-refill
     */
    public static function getNextEnergyTime($characterId)
    {
        $data = self::getData($characterId);
        
        if ($data['energy'] >= self::MAX_ENERGY) {
            return null; // Sudah full
        }
        
        $lastEnergyTime = $data['last_energy_reset'];
        $nextEnergyTime = $lastEnergyTime->copy()->addMinutes(self::ENERGY_REFILL_MINUTES);
        
        return $nextEnergyTime->toISOString();
    }

    /**
     * Get berapa menit lagi untuk energy berikutnya
     */
    public static function getMinutesToNextEnergy($characterId)
    {
        $data = self::getData($characterId);
        
        if ($data['energy'] >= self::MAX_ENERGY) {
            return 0;
        }
        
        $lastEnergyTime = $data['last_energy_reset'];
        $nextEnergyTime = $lastEnergyTime->copy()->addMinutes(self::ENERGY_REFILL_MINUTES);
        $now = Carbon::now();
        
        return max(0, $now->diffInMinutes($nextEnergyTime, false));
    }

    /**
     * Clear data (untuk testing)
     */
    public static function clearData($characterId)
    {
        $sessionKey = self::SESSION_KEY_PREFIX . $characterId;
        Session::forget($sessionKey);
        Log::info("PhantomKyunoki: Cleared session data for char $characterId");
    }
}