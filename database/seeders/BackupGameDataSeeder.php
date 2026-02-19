<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Item;
use App\Models\Skill;
use App\Models\Pet;
use App\Models\Mission;
use App\Models\XP;

class BackupGameDataSeeder extends Seeder
{
    public function run(): void
    {
        // 1. Items
        $items = [
            "wpn_01" => ["name" => "Kunai", "level" => 1, "price_gold" => 100, "price_tokens" => 0, "category" => "weapon"],
            "wpn_02" => ["name" => "Shuriken", "level" => 5, "price_gold" => 500, "price_tokens" => 0, "category" => "weapon"],
            "set_01_0" => ["name" => "Rookie Set (M)", "level" => 1, "price_gold" => 200, "price_tokens" => 0, "category" => "set"],
            "set_01_1" => ["name" => "Rookie Set (F)", "level" => 1, "price_gold" => 200, "price_tokens" => 0, "category" => "set"],
            "hair_01_0" => ["name" => "Spiky (M)", "level" => 1, "price_gold" => 50, "price_tokens" => 0, "category" => "hair"],
            "hair_01_1" => ["name" => "Long (F)", "level" => 1, "price_gold" => 50, "price_tokens" => 0, "category" => "hair"],
            "back_01" => ["name" => "Scroll", "level" => 1, "price_gold" => 150, "price_tokens" => 0, "category" => "back"],
            "accessory_01" => ["name" => "Headband", "level" => 1, "price_gold" => 100, "price_tokens" => 0, "category" => "accessory"],
            "item_45" => ["name" => "Healing Scroll", "level" => 1, "price_gold" => 50, "price_tokens" => 0, "category" => "item"],
            "essential_01" => ["name" => "Chakra Pill", "level" => 1, "price_gold" => 100, "price_tokens" => 0, "category" => "essential"],
            "essential_05" => ["name" => "Teleport Scroll", "level" => 1, "price_gold" => 20, "price_tokens" => 0, "category" => "essential"],
            "essential_12" => ["name" => "Smoke Bomb", "level" => 5, "price_gold" => 50, "price_tokens" => 0, "category" => "essential"],
        ];
        
        foreach ($items as $id => $data) {
            Item::updateOrCreate(['item_id' => $id], [
                'name' => $data['name'],
                'level' => $data['level'],
                'price_gold' => $data['price_gold'],
                'price_tokens' => $data['price_tokens'],
                'category' => $data['category'],
                'premium' => $data['premium'] ?? false,
            ]);
        }

        // 2. Skills
        $skills = [
            "skill_01" => ["name" => "Lightning Edge", "level" => 1, "element" => 3, "price_gold" => 0, "price_tokens" => 0],
            "skill_02" => ["name" => "Quick Strike", "level" => 1, "element" => 0, "price_gold" => 0, "price_tokens" => 0],
            "skill_09" => ["name" => "Water Dragon", "level" => 1, "element" => 5, "price_gold" => 0, "price_tokens" => 0],
            "skill_10" => ["name" => "Fireball", "level" => 1, "element" => 2, "price_gold" => 0, "price_tokens" => 0],
            "skill_12" => ["name" => "Earth Wall", "level" => 1, "element" => 4, "price_gold" => 0, "price_tokens" => 0],
            "skill_13" => ["name" => "Wind Blade", "level" => 1, "element" => 1, "price_gold" => 0, "price_tokens" => 0],
            "skill_2158" => ["name" => "Secret Technique", "level" => 10, "element" => 0, "price_gold" => 1000, "price_tokens" => 0],
        ];

        foreach ($skills as $id => $data) {
            Skill::updateOrCreate(['skill_id' => $id], [
                'name' => $data['name'],
                'level' => $data['level'],
                'element' => $data['element'],
                'price_gold' => $data['price_gold'],
                'price_tokens' => $data['price_tokens'],
                'premium' => $data['premium'] ?? false,
            ]);
        }

        // 3. Pets
        $pets = [
            "26941" => ["name" => "Easter Rokubi", "swf" => "pet_easterrokubi", "price_gold" => 100000, "price_tokens" => 0, "premium" => false],
            "pet_01" => ["name" => "Eri", "swf" => "pet_01", "price_gold" => 50000, "price_tokens" => 0, "premium" => false],
            "pet_02" => ["name" => "Leira", "swf" => "pet_02", "price_gold" => 0, "price_tokens" => 500, "premium" => false],
            "pet_easa" => ["name" => "Easter Sabertooth", "swf" => "pet_easa", "price_gold" => 100000, "price_tokens" => 0, "premium" => true],
        ];

        foreach ($pets as $id => $data) {
            Pet::updateOrCreate(['pet_id' => $id], [
                'name' => $data['name'],
                'swf' => $data['swf'],
                'price_gold' => $data['price_gold'],
                'price_tokens' => $data['price_tokens'],
                'premium' => $data['premium'] ?? false,
            ]);
        }

        // 4. Missions
        $missions = [
            "msn_01" => ["req_lvl" => 1, "xp" => 50, "gold" => 100],
            "msn_02" => ["req_lvl" => 2, "xp" => 100, "gold" => 200],
            "msn_03" => ["req_lvl" => 3, "xp" => 150, "gold" => 300],
        ];

        foreach ($missions as $id => $data) {
            Mission::updateOrCreate(['mission_id' => $id], [
                'req_lvl' => $data['req_lvl'],
                'xp' => $data['xp'],
                'gold' => $data['gold'],
            ]);
        }

        // 5. XP
        $characterXp = [
            1 => 15, 2 => 304, 3 => 493, 4 => 711, 5 => 961, 6 => 1247, 7 => 1574, 8 => 1945, 9 => 2366, 10 => 2843,
            11 => 3382, 12 => 3989, 13 => 4673, 14 => 5542, 15 => 6306, 16 => 7273, 17 => 8537, 18 => 9569, 19 => 10922, 20 => 12433,
            21 => 14117, 22 => 15992, 23 => 18080, 24 => 20401, 25 => 22981, 26 => 25845, 27 => 29024, 28 => 32548, 29 => 36454, 30 => 40780,
            31 => 45569, 32 => 50867, 33 => 56725, 34 => 63201, 35 => 70354, 36 => 78254, 37 => 86973, 38 => 96593, 39 => 107202, 40 => 118899,
            41 => 131790, 42 => 145991, 43 => 161632, 44 => 178850, 45 => 197801, 46 => 218652, 47 => 241587, 48 => 266806, 49 => 294530, 50 => 325000,
            51 => 358478, 52 => 395253, 53 => 435640, 54 => 479982, 55 => 528656, 56 => 582073, 57 => 640648, 58 => 704980, 59 => 775497, 60 => 858822,
            61 => 973598, 62 => 1030523, 63 => 1132364, 64 => 1243956, 65 => 1366211, 66 => 1500266, 67 => 1646789, 68 => 1807388, 69 => 1983211, 70 => 2175702,
            71 => 3857490, 72 => 5539279, 73 => 7221067, 74 => 8902856, 75 => 10584644, 76 => 34958287, 77 => 38667739, 78 => 42377192, 79 => 46086644, 80 => 49796096,
            81 => 69149957, 82 => 73172858, 83 => 77195758, 84 => 81218659, 85 => 85241560
        ];

        $petXp = [
            1 => 28, 2 => 61, 3 => 99, 4 => 142, 5 => 192, 6 => 249, 7 => 315, 8 => 389, 9 => 473, 10 => 569,
            11 => 676, 12 => 798, 13 => 935, 14 => 1088, 15 => 1261, 16 => 1455, 17 => 1671, 18 => 1914, 19 => 2184, 20 => 2487,
            21 => 2823, 22 => 3198, 23 => 3616, 24 => 4080, 25 => 4596, 26 => 5196, 27 => 5805, 28 => 6510, 29 => 7291, 30 => 8156,
            31 => 9114, 32 => 10173, 33 => 11345, 34 => 12640, 35 => 14071, 36 => 15651, 37 => 17395, 38 => 19319, 39 => 21440, 40 => 23780,
            41 => 27733, 42 => 30696, 43 => 33471, 44 => 36193, 45 => 39579, 46 => 42140, 47 => 46342, 48 => 49634, 49 => 53379, 50 => 56695,
            51 => 59936, 52 => 66622, 53 => 70841, 54 => 74605, 55 => 79734, 56 => 86755, 57 => 90227, 58 => 95427, 59 => 103740, 60 => 110291,
            61 => 125307, 62 => 145705, 63 => 174070, 64 => 211985, 65 => 259748, 66 => 314393, 67 => 377280, 68 => 447571, 69 => 526381, 70 => 612222,
            71 => 705963, 72 => 806478, 73 => 912730, 74 => 1026380, 75 => 1144886, 76 => 1269847, 77 => 1402425, 78 => 1538415, 79 => 1683103, 80 => 1831845,
            81 => 2049957, 82 => 2372858, 83 => 2695758, 84 => 3018659, 85 => 3541560
        ];

        foreach ($characterXp as $level => $xp) {
            XP::updateOrCreate(['level' => $level], [
                'character_xp' => $xp,
                'pet_xp' => $petXp[$level] ?? 999999999,
            ]);
        }
    }
}