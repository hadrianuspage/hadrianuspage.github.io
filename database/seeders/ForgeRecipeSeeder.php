<?php

namespace Database\Seeders;

use App\Models\ForgeRecipe;
use Illuminate\Database\Seeder;

class ForgeRecipeSeeder extends Seeder
{
    public function run()
    {
        $recipes = [
            // Hair
            ['item_id' => 'hair_2356_%s', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [50, 20], 'category' => 'hair', 'end_date' => '2026-12-31'],
            ['item_id' => 'hair_2357_%s', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [50, 20], 'category' => 'hair', 'end_date' => '2026-12-31'],
            ['item_id' => 'hair_2358_%s', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [50, 20], 'category' => 'hair', 'end_date' => '2026-12-31'],
            ['item_id' => 'hair_2359_%s', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [50, 20], 'category' => 'hair', 'end_date' => '2026-12-31'],

            // Sets
            ['item_id' => 'set_2396_%s', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [100, 30], 'category' => 'set', 'end_date' => '2026-12-31'],
            ['item_id' => 'set_2397_%s', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [100, 30], 'category' => 'set', 'end_date' => '2026-12-31'],
            ['item_id' => 'set_2398_%s', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [100, 30], 'category' => 'set', 'end_date' => '2026-12-31'],
            ['item_id' => 'set_2399_%s', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [100, 30], 'category' => 'set', 'end_date' => '2026-12-31'],

            // Backs
            ['item_id' => 'back_2390', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [80, 25], 'category' => 'back', 'end_date' => '2026-12-31'],
            ['item_id' => 'back_2391', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [80, 25], 'category' => 'back', 'end_date' => '2026-12-31'],
            ['item_id' => 'back_2392', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [80, 25], 'category' => 'back', 'end_date' => '2026-12-31'],
            ['item_id' => 'back_2393', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [80, 25], 'category' => 'back', 'end_date' => '2026-12-31'],

            // Weapons
            ['item_id' => 'wpn_2393', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [120, 35], 'category' => 'wpn', 'end_date' => '2026-12-31'],
            ['item_id' => 'wpn_2394', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [120, 35], 'category' => 'wpn', 'end_date' => '2026-12-31'],
            ['item_id' => 'wpn_2395', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [120, 35], 'category' => 'wpn', 'end_date' => '2026-12-31'],
            ['item_id' => 'wpn_2396', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [120, 35], 'category' => 'wpn', 'end_date' => '2026-12-31'],

            // Skills
            ['item_id' => 'skill_2318', 'materials' => ['material_2221', 'material_2222', 'material_2223'], 'quantities' => [150, 40, 40], 'category' => 'skill', 'end_date' => '2026-12-31'],
            ['item_id' => 'skill_2319', 'materials' => ['material_2221', 'material_2223', 'material_2224'], 'quantities' => [150, 40, 40], 'category' => 'skill', 'end_date' => '2026-12-31'],
            ['item_id' => 'skill_2320', 'materials' => ['material_2221', 'material_2224', 'material_2225'], 'quantities' => [150, 40, 40], 'category' => 'skill', 'end_date' => '2026-12-31'],
            ['item_id' => 'skill_2321', 'materials' => ['material_2221', 'material_2222', 'material_2225'], 'quantities' => [150, 40, 40], 'category' => 'skill', 'end_date' => '2026-12-31'],
        ];

        foreach ($recipes as $recipe) {
            ForgeRecipe::create($recipe);
        }
    }
}
