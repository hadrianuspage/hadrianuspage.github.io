<?php
// Create file: database/seeders/MissionSeeder.php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\File;

class MissionSeeder extends Seeder
{
    public function run()
    {
        // Read mission.json
        $path = base_path('public/game_data/mission.json');
        $content = File::get($path);
        $missions = json_decode($content, true);

        foreach ($missions as $mission) {
            DB::table('missions')->updateOrInsert(
                ['mission_id' => $mission['id']],
                [
                    'mission_id' => $mission['id'],
                    'req_lvl' => $mission['level'],
                    'xp' => $mission['rewards']['xp'],
                    'gold' => $mission['rewards']['gold'],
                    'created_at' => now(),
                    'updated_at' => now(),
                ]
            );
        }

        $this->command->info('Missions imported successfully!');
    }
}