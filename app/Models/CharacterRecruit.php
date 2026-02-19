<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class CharacterRecruit extends Model
{
    use HasFactory;

    protected $fillable = [
        'character_id',
        'recruit_id'
    ];
    
    // Add relationships for easier debugging
    public function character()
    {
        return $this->belongsTo(Character::class);
    }
    
    public function getRecruitedCharacter()
    {
        if (str_starts_with($this->recruit_id, 'char_')) {
            $friendId = substr($this->recruit_id, 5);
            return Character::find($friendId);
        }
        return null;
    }
    
    public function getRecruitedNpc()
    {
        if (!str_starts_with($this->recruit_id, 'char_')) {
            return Npc::where('npc_id', $this->recruit_id)
                     ->orWhere('npc_id', 'npc_' . $this->recruit_id)
                     ->first();
        }
        return null;
    }
}

