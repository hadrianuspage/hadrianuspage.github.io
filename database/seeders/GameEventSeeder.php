<?php

use Illuminate\Database\Seeder;
use App\Models\GameEvent;

class GameEventSeeder extends Seeder
{
    public function run()
    {
        GameEvent::create([
            'title' => 'Yuki Onna: Eternal Winter',
            'type' => 'seasonal',
            'image_url' => 'https://ns-assets.ninjasage.id/tmp/yukionna.jpg',
            'description' => 'Fight back the blizzard and stop the Eternal Winter.',
            'active' => true,
            'data' => [
                'date' => '25/12 - 25/03, 2026',
                'panel' => 'ChristmasMenu'
            ]
        ]);
    }
}