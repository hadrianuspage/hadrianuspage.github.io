<?php

namespace App\Models;

class HuntingHouseItem
{
    private static $recipes = [
        // Original Hunting House Items (1-18)
        ['item_id' => 'wpn_6031',      'materials' => ['material_01', 'material_02', 'material_509'], 'quantities' => [10, 5, 2],   'sort_order' => 1],
        ['item_id' => 'wpn_2175',      'materials' => ['material_02', 'material_03', 'material_509'], 'quantities' => [15, 10, 3],  'sort_order' => 2],
        ['item_id' => 'wpn_2139',      'materials' => ['material_03', 'material_04', 'material_509'], 'quantities' => [20, 15, 5],  'sort_order' => 3],
        ['item_id' => 'wpn_8069',      'materials' => ['material_04', 'material_05', 'material_509'], 'quantities' => [25, 20, 8],  'sort_order' => 4],
        ['item_id' => 'wpn_2285',      'materials' => ['material_01', 'material_05', 'material_509'], 'quantities' => [30, 25, 10], 'sort_order' => 5],
        ['item_id' => 'back_2333',     'materials' => ['material_03', 'material_04', 'material_509'], 'quantities' => [15, 10, 3],  'sort_order' => 6],
        ['item_id' => 'set_7025_0',    'materials' => ['material_02', 'material_04', 'material_509'], 'quantities' => [20, 15, 5],  'sort_order' => 7],
        ['item_id' => 'set_7025_1',    'materials' => ['material_03', 'material_05', 'material_509'], 'quantities' => [20, 15, 5],  'sort_order' => 8],
        ['item_id' => 'hair_2074_0',   'materials' => ['material_01', 'material_03', 'material_509'], 'quantities' => [10, 8, 2],   'sort_order' => 9],
        ['item_id' => 'hair_2074_1',   'materials' => ['material_02', 'material_04', 'material_509'], 'quantities' => [10, 8, 2],   'sort_order' => 10],
        ['item_id' => 'accessory_2003','materials' => ['material_03', 'material_04', 'material_05'],  'quantities' => [12, 8, 5],   'sort_order' => 11],
        ['item_id' => 'pet_moyai',     'materials' => ['material_03', 'material_04', 'material_05', 'material_509'], 'quantities' => [30, 15, 10, 5], 'sort_order' => 12],
        ['item_id' => 'material_509',  'materials' => ['material_03', 'material_04', 'material_05'], 'quantities' => [5, 3, 2],    'sort_order' => 13],
        ['item_id' => 'skill_7000',    'materials' => ['material_01', 'material_02'],                'quantities' => [5, 3],        'sort_order' => 14],
        ['item_id' => 'skill_7045',    'materials' => ['material_02', 'material_03'],                'quantities' => [8, 5],        'sort_order' => 15],
        ['item_id' => 'skill_2273',    'materials' => ['material_03', 'material_04'],                'quantities' => [12, 8],       'sort_order' => 16],
        ['item_id' => 'skill_2151',    'materials' => ['material_04', 'material_05'],                'quantities' => [15, 10],      'sort_order' => 17],
        ['item_id' => 'skill_566',     'materials' => ['material_01', 'material_03', 'material_509'],'quantities' => [20, 15, 5],   'sort_order' => 18],

        // NEW: Thanksgiving Hair (19-26)
        ['item_id' => 'hair_2356_0', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [50, 20], 'sort_order' => 19],
        ['item_id' => 'hair_2357_0', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [50, 20], 'sort_order' => 20],
        ['item_id' => 'hair_2358_0', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [50, 20], 'sort_order' => 21],
        ['item_id' => 'hair_2359_0', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [50, 20], 'sort_order' => 22],
        ['item_id' => 'hair_2356_1', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [50, 20], 'sort_order' => 23],
        ['item_id' => 'hair_2357_1', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [50, 20], 'sort_order' => 24],
        ['item_id' => 'hair_2358_1', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [50, 20], 'sort_order' => 25],
        ['item_id' => 'hair_2359_1', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [50, 20], 'sort_order' => 26],

        // NEW: Thanksgiving Sets (27-34)
        ['item_id' => 'set_2396_0', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [100, 30], 'sort_order' => 27],
        ['item_id' => 'set_2397_0', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [100, 30], 'sort_order' => 28],
        ['item_id' => 'set_2398_0', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [100, 30], 'sort_order' => 29],
        ['item_id' => 'set_2399_0', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [100, 30], 'sort_order' => 30],
        ['item_id' => 'set_2396_1', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [100, 30], 'sort_order' => 31],
        ['item_id' => 'set_2397_1', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [100, 30], 'sort_order' => 32],
        ['item_id' => 'set_2398_1', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [100, 30], 'sort_order' => 33],
        ['item_id' => 'set_2399_1', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [100, 30], 'sort_order' => 34],

        // NEW: Thanksgiving Backs (35-38)
        ['item_id' => 'back_2390', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [80, 25], 'sort_order' => 35],
        ['item_id' => 'back_2391', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [80, 25], 'sort_order' => 36],
        ['item_id' => 'back_2392', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [80, 25], 'sort_order' => 37],
        ['item_id' => 'back_2393', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [80, 25], 'sort_order' => 38],

        // NEW: Thanksgiving Weapons (39-42)
        ['item_id' => 'wpn_2393', 'materials' => ['material_2221', 'material_2222'], 'quantities' => [120, 35], 'sort_order' => 39],
        ['item_id' => 'wpn_2394', 'materials' => ['material_2221', 'material_2223'], 'quantities' => [120, 35], 'sort_order' => 40],
        ['item_id' => 'wpn_2395', 'materials' => ['material_2221', 'material_2224'], 'quantities' => [120, 35], 'sort_order' => 41],
        ['item_id' => 'wpn_2396', 'materials' => ['material_2221', 'material_2225'], 'quantities' => [120, 35], 'sort_order' => 42],

        // NEW: Thanksgiving Skills (43-46)
        ['item_id' => 'skill_2318', 'materials' => ['material_2221', 'material_2222', 'material_2223'], 'quantities' => [150, 40, 40], 'sort_order' => 43],
        ['item_id' => 'skill_2319', 'materials' => ['material_2221', 'material_2223', 'material_2224'], 'quantities' => [150, 40, 40], 'sort_order' => 44],
        ['item_id' => 'skill_2320', 'materials' => ['material_2221', 'material_2224', 'material_2225'], 'quantities' => [150, 40, 40], 'sort_order' => 45],
        ['item_id' => 'skill_2321', 'materials' => ['material_2221', 'material_2222', 'material_2225'], 'quantities' => [150, 40, 40], 'sort_order' => 46],

        // NEW: Thanksgiving Pet (47)
        ['item_id' => 'pet_karasutengu', 'materials' => ['material_2221', 'material_2223', 'material_2225'], 'quantities' => [100, 50, 50], 'sort_order' => 47],

        // NEW: Phantom Kyunoki Event (48-54)
        ['item_id' => 'wpn_2409', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [52, 30, 22, 12], 'sort_order' => 48],
        ['item_id' => 'back_2407', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [46, 22, 16, 8], 'sort_order' => 49],
        ['item_id' => 'hair_2375_0', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [22, 16, 10, 5], 'sort_order' => 50],
        ['item_id' => 'hair_2375_1', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [22, 16, 10, 5], 'sort_order' => 51],
        ['item_id' => 'set_2416_0', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [38, 22, 16, 5], 'sort_order' => 52],
        ['item_id' => 'set_2416_1', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [38, 22, 16, 5], 'sort_order' => 53],
        ['item_id' => 'skill_726', 'materials' => ['material_2232', 'material_2233', 'material_2234', 'material_2235'], 'quantities' => [15, 10, 8, 5], 'sort_order' => 54],

        // NEW: Confronting Death Event 2025 (55-62)
        ['item_id' => 'hair_2351_0', 'materials' => ['material_2216', 'material_2217', 'material_2218'], 'quantities' => [25, 15, 10], 'sort_order' => 55],
        ['item_id' => 'hair_2351_1', 'materials' => ['material_2216', 'material_2217', 'material_2218'], 'quantities' => [25, 15, 10], 'sort_order' => 56],
        ['item_id' => 'hair_2352_0', 'materials' => ['material_2216', 'material_2217', 'material_2219'], 'quantities' => [25, 15, 10], 'sort_order' => 57],
        ['item_id' => 'hair_2352_1', 'materials' => ['material_2216', 'material_2217', 'material_2219'], 'quantities' => [25, 15, 10], 'sort_order' => 58],
        ['item_id' => 'set_2391_0', 'materials' => ['material_2216', 'material_2217', 'material_2218', 'material_2219'], 'quantities' => [50, 30, 20, 15], 'sort_order' => 59],
        ['item_id' => 'set_2391_1', 'materials' => ['material_2216', 'material_2217', 'material_2218', 'material_2219'], 'quantities' => [50, 30, 20, 15], 'sort_order' => 60],
        ['item_id' => 'set_2392_0', 'materials' => ['material_2216', 'material_2218', 'material_2219', 'material_2220'], 'quantities' => [50, 30, 20, 15], 'sort_order' => 61],
        ['item_id' => 'set_2392_1', 'materials' => ['material_2216', 'material_2218', 'material_2219', 'material_2220'], 'quantities' => [50, 30, 20, 15], 'sort_order' => 62],

        // NEW: Confronting Death Backs (63-65)
        ['item_id' => 'back_2384', 'materials' => ['material_2216', 'material_2217', 'material_2218'], 'quantities' => [40, 25, 15], 'sort_order' => 63],
        ['item_id' => 'back_2385', 'materials' => ['material_2217', 'material_2218', 'material_2219'], 'quantities' => [40, 25, 15], 'sort_order' => 64],
        ['item_id' => 'back_2386', 'materials' => ['material_2218', 'material_2219', 'material_2220'], 'quantities' => [40, 25, 15], 'sort_order' => 65],

        // NEW: Confronting Death Weapons (66-68)
        ['item_id' => 'wpn_2387', 'materials' => ['material_2216', 'material_2217', 'material_2218', 'material_2219'], 'quantities' => [60, 35, 25, 20], 'sort_order' => 66],
        ['item_id' => 'wpn_2388', 'materials' => ['material_2217', 'material_2218', 'material_2219', 'material_2220'], 'quantities' => [60, 35, 25, 20], 'sort_order' => 67],
        ['item_id' => 'wpn_2389', 'materials' => ['material_2216', 'material_2218', 'material_2220'], 'quantities' => [60, 35, 25], 'sort_order' => 68],

        // NEW: Confronting Death Skills (69-70)
        ['item_id' => 'skill_2311', 'materials' => ['material_2216', 'material_2217', 'material_2218', 'material_2219', 'material_2220'], 'quantities' => [80, 50, 35, 25, 15], 'sort_order' => 69],
        ['item_id' => 'skill_2312', 'materials' => ['material_2216', 'material_2217', 'material_2218', 'material_2219', 'material_2220'], 'quantities' => [80, 50, 35, 25, 15], 'sort_order' => 70],
    ];

    public $item_id;
    public $materials;
    public $quantities;
    public $sort_order;
    private $search_column;
    private $search_value;

    public function __construct($attributes = [])
    {
        $this->item_id      = $attributes['item_id']      ?? null;
        $this->materials    = $attributes['materials']    ?? [];
        $this->quantities   = $attributes['quantities']   ?? [];
        $this->sort_order   = $attributes['sort_order']   ?? 0;
        $this->search_column = $attributes['search_column'] ?? null;
        $this->search_value  = $attributes['search_value']  ?? null;
    }

    public static function orderBy($column)
    {
        $instance = new static();
        $instance->search_column = 'orderBy';
        $instance->search_value  = $column;
        return $instance;
    }

    public function get()
    {
        $results = [];
        foreach (self::$recipes as $recipe) {
            $results[] = new self($recipe);
        }

        if ($this->search_column === 'orderBy') {
            usort($results, function ($a, $b) {
                return $a->sort_order <=> $b->sort_order;
            });
        }

        return $results;
    }

    public static function where($column, $value)
    {
        return new static(['search_column' => $column, 'search_value' => $value]);
    }

    public function first()
    {
        if ($this->search_column && $this->search_value) {
            foreach (self::$recipes as $recipe) {
                if ($recipe[$this->search_column] == $this->search_value) {
                    return new self($recipe);
                }
            }
        }
        return null;
    }
}