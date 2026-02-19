<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class CharacterThanksgivingEvent extends Model
{
    protected $table = 'character_thanksgiving_events';

    protected $fillable = [
        'character_id',
        'energy',
        'battles_count',
        'last_battle_date',
        'last_energy_reset',
        'claimed_milestone_rewards',
        'package_bought'
    ];

    protected $casts = [
        'energy' => 'integer',
        'battles_count' => 'integer',
        'package_bought' => 'boolean',
        'last_battle_date' => 'datetime',
        'last_energy_reset' => 'datetime'
    ];

    private const MAX_ENERGY = 10;
    private const ENERGY_REFILL_MINUTES = 20; // 20 menit per energy

    /**
     * Relationship to Character
     */
    public function character()
    {
        return $this->belongsTo(Character::class);
    }

    /**
     * Get claimed rewards as array
     */
    public function getClaimedRewardsArray()
    {
        if (empty($this->claimed_milestone_rewards)) {
            return array_fill(0, 8, false);
        }

        $claimed = json_decode($this->claimed_milestone_rewards, true);
        
        if (!is_array($claimed)) {
            return array_fill(0, 8, false);
        }

        // Ensure array has 8 elements
        while (count($claimed) < 8) {
            $claimed[] = false;
        }

        return $claimed;
    }

    /**
     * Set claimed rewards from array
     */
    public function setClaimedRewardsArray($array)
    {
        $this->claimed_milestone_rewards = json_encode($array);
    }

    /**
     * Auto refill energy berdasarkan waktu (20 menit per energy)
     */
    public function autoRefillEnergy()
    {
        if ($this->energy >= self::MAX_ENERGY) {
            return; // Sudah full
        }

        $lastEnergyTime = $this->last_energy_reset ? Carbon::parse($this->last_energy_reset) : Carbon::now();
        $now = Carbon::now();
        
        // Hitung berapa menit yang sudah lewat
        $minutesPassed = $now->diffInMinutes($lastEnergyTime);
        
        // Setiap 20 menit = 1 energy
        $energyToAdd = floor($minutesPassed / self::ENERGY_REFILL_MINUTES);
        
        if ($energyToAdd > 0) {
            $oldEnergy = $this->energy;
            $this->energy = min(self::MAX_ENERGY, $this->energy + $energyToAdd);
            
            // Update waktu dengan sisa menit yang belum cukup untuk 1 energy
            $remainingMinutes = $minutesPassed % self::ENERGY_REFILL_MINUTES;
            $this->last_energy_reset = $now->subMinutes($remainingMinutes);
            $this->save();
            
            Log::info("ThanksGiving Auto refilled energy: {$oldEnergy} -> {$this->energy} (+{$energyToAdd})");
        }
    }

    /**
     * Check if needs daily energy reset
     */
    public function checkDailyReset()
    {
        $today = Carbon::today();
        $lastReset = $this->last_energy_reset ? Carbon::parse($this->last_energy_reset)->startOfDay() : null;
        
        if (!$lastReset || $lastReset->lt($today)) {
            $this->energy = self::MAX_ENERGY;
            $this->last_energy_reset = Carbon::now();
            $this->save();
            
            Log::info("ThanksGiving Daily energy reset: Energy set to " . self::MAX_ENERGY);
        }
    }

    /**
     * Increment battle count
     */
    public function incrementBattles()
    {
        $this->battles_count++;
        $this->last_battle_date = now();
        $this->save();
    }

    /**
     * Use energy
     */
    public function useEnergy($amount = 1)
    {
        if ($this->energy >= $amount) {
            $this->energy -= $amount;
            $this->save();
            
            Log::info("ThanksGiving Energy used: -{$amount}, remaining: {$this->energy}");
            return true;
        }
        return false;
    }

    /**
     * Refill energy dengan token (langsung full)
     */
    public function refillEnergyWithToken()
    {
        $this->energy = self::MAX_ENERGY;
        $this->last_energy_reset = Carbon::now();
        $this->save();
        
        Log::info("ThanksGiving Energy refilled with token: Full " . self::MAX_ENERGY);
    }

    /**
     * Get waktu kapan energy berikutnya akan di-refill
     */
    public function getNextEnergyTime()
    {
        if ($this->energy >= self::MAX_ENERGY) {
            return null; // Sudah full
        }
        
        $lastEnergyTime = $this->last_energy_reset ? Carbon::parse($this->last_energy_reset) : Carbon::now();
        $nextEnergyTime = $lastEnergyTime->addMinutes(self::ENERGY_REFILL_MINUTES);
        
        return $nextEnergyTime->toISOString();
    }

    /**
     * Get berapa menit lagi untuk energy berikutnya
     */
    public function getMinutesToNextEnergy()
    {
        if ($this->energy >= self::MAX_ENERGY) {
            return 0;
        }
        
        $lastEnergyTime = $this->last_energy_reset ? Carbon::parse($this->last_energy_reset) : Carbon::now();
        $nextEnergyTime = $lastEnergyTime->addMinutes(self::ENERGY_REFILL_MINUTES);
        $now = Carbon::now();
        
        return max(0, $now->diffInMinutes($nextEnergyTime, false));
    }
}

