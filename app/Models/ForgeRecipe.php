<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ForgeRecipe extends Model
{
    protected $fillable = [
        'item_id',
        'materials',
        'quantities',
        'end_date',
        'category'
    ];

    protected $casts = [
        'materials' => 'array',
        'quantities' => 'array',
        'end_date' => 'date'
    ];
}
