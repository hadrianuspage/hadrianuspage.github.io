<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class CharacterHuntingHouse extends Model
{
    use HasFactory;

    protected $table = 'character_hunting_houses';

    protected $fillable = [
        'character_id',
        'last_daily_claim_date',
    ];

    protected $dates = [
        'last_daily_claim_date',
        'created_at',
        'updated_at',
    ];

    public function character()
    {
        return $this->belongsTo(Character::class);
    }
}

