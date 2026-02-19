<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class GameEvent extends Model
{
    use HasFactory;

    protected $fillable = [
        'title',
        'type',
        'image_url',
        'description',
        'active',
        'data',
    ];

    protected $casts = [
        'active' => 'boolean',
        'data' => 'array',
    ];
}