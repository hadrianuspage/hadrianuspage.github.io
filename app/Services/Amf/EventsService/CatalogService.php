<?php

namespace App\Services\Amf\EventsService;

use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class CatalogService
{
    use ValidatesSession;

    /**
     * get
     * Params: None (or possibly sessionKey/charId but passed as null in ImageDownloadTask)
     */
    public function get($params = null)
    {
        if (is_array($params) && isset($params[0], $params[1])) {
            $guard = $this->guardCharacterSession((int)$params[0], $params[1]);
            if ($guard) {
                return $guard;
            }
        }

        Log::info("AMF EventsService.get");

        return [
            'status' => 1,
            'error' => 0,
            'events' => [
                'seasonal' => [
                    //[
                        //'name' => 'Yuki Onna: Eternal Winter',
                        //'desc' => 'Fight back the blizzard and stop the Eternal Winter before the Christmas Star fades away.',
                        //'date' => '25/12 - 25/03, 2024',
                        //'img' => 'https://ns-assets.ninjasage.id/tmp/yukionna.jpg',
                        //'panel' => 'ChristmasMenu',
                    //],
                    [
                        'name' => 'Feast of Gratitude: Celebration',
                        'desc' => 'Ninjas must compete, collect, and defend the feast to ensure every villager enjoys the celebration.',
                        'date' => '02/17 - 05/17, 2026',
                        'img' => 'https://i.ibb.co.com/Y47r1npY/thanksgiving2025.jpg',
                        'panel' => 'FeastOfGratitudeMenu',
                    ],
                     [
                        'name' => 'Phantom Kyunoki: The Unsealed Beast',
                        'desc' => 'As the dead rise, the ninjas must unite to face Phantom Kyunoki.',
                        'date' => '02/17 - 05/17, 2026',
                        'img' => 'https://i.ibb.co.com/G3MJ2drx/phantom-kyunoki-2026-G3r-C0.png',
                        'panel' => 'PhantomKyunokiMenu',
                    ],
                    [
                        'name' => 'Confronting Death Event 2025',
                        'desc' => 'Lord of the Underworld is the ruler of the underworld. He is the one who controls the dead and the living. He is the one who controls the fate of the world.',
                        'date' => '04/11 - 04/02, 2025',
                        'img' => 'https://i.ibb.co.com/1tYb24LQ/confrontingdeath2025.jpg',
                        'panel' => 'ConfrontingDeathMenu',
                    ],
                ],
                'event:permanent' => [
                    ['name' => 'Monster Hunter', 'icon' => 'monsterhunter', 'panel' => 'MonsterHunter'],
                    ['name' => 'Dragon Hunt', 'icon' => 'dragonhunt', 'panel' => 'DragonHunt'],
                    ['name' => 'Justice Badge', 'icon' => 'justicebadge', 'panel' => 'JusticeBadge'],
                ],
                'features' => [
                    ['name' => 'Giveaway Center', 'icon' => 'giveaway', 'panel' => 'GiveawayCenter'],
                    ['name' => 'Leaderboard', 'icon' => 'leaderboard', 'panel' => 'Leaderboard'],
                    ['name' => 'Tailed Beast', 'icon' => 'tailedbeast', 'panel' => 'TailedBeast', 'inside' => true],
                    ['name' => 'Daily Gacha', 'icon' => 'dailygacha', 'panel' => 'DailyGacha'],
                    ['name' => 'Dragon Gacha', 'icon' => 'dragongacha', 'panel' => 'DragonGacha'],
                    ['name' => 'Exotic Package', 'icon' => 'exotic', 'panel' => 'ExoticPackage'],
                ],
                'packages' => [
                    'name' => 'Elemental Ars Package',
                    'date' => '15/04 - 05/03, 2026',
                    'content' => [
                        [
                            'name' => 'Codex Elementia',
                            'price' => 'IDR. 100,000',
                            'outfits' => [
                                'ani' => [null],
                                'pet' => [null],
                                'set' => ['set_2402_%s'],
                                'back' => ['back_2396'],
                                'hair' => ['hair_2361_%s'],
                                'skill' => [null],
                                'weapon' => [null],
                                'accessory' => [null],
                            ],
                            'rewards' => ['hair_2361_%s', 'back_2396', 'set_2402_%s', 'emblem', 'tokens_4500'],
                        ],
                        [
                            'name' => 'Grimoire Arcanum',
                            'price' => 'IDR. 250,000',
                            'outfits' => [
                                'ani' => [null],
                                'pet' => [null],
                                'set' => ['set_2402_%s', 'set_2401_%s'],
                                'back' => ['back_2396'],
                                'hair' => ['hair_2361_%s'],
                                'skill' => ['skill_2323'],
                                'weapon' => [null],
                                'accessory' => [null],
                            ],
                            'rewards' => [
                                'hair_2361_%s',
                                'set_2402_%s',
                                'set_2401_%s',
                                'back_2396',
                                'skill_2323',
                                'emblem',
                                'tokens_10250',
                            ],
                        ],
                        [
                            'name' => 'Elementis Corcondia',
                            'price' => 'IDR. 500,000',
                            'outfits' => [
                                'ani' => [null],
                                'pet' => ['pet_ancientgolem'],
                                'set' => ['set_2402_%s', 'set_2401_%s'],
                                'back' => ['back_2396'],
                                'hair' => ['hair_2361_%s'],
                                'skill' => ['skill_2323', 'skill_2324'],
                                'weapon' => ['wpn_2399'],
                                'accessory' => [null],
                            ],
                            'rewards' => [
                                'hair_2361_%s',
                                'set_2402_%s',
                                'set_2401_%s',
                                'back_2396',
                                'wpn_2399',
                                'pet_ancientgolem',
                                'skill_2323',
                                'skill_2324',
                                'emblem',
                                'tokens_21000',
                            ],
                        ],
                        [
                            'name' => 'Tomea Astralis',
                            'price' => 'IDR. 1,000,000',
                            'outfits' => [
                                'ani' => [null],
                                'pet' => ['pet_ancientgolem'],
                                'set' => ['set_2402_%s', 'set_2401_%s'],
                                'back' => ['back_2396'],
                                'hair' => ['hair_2361_%s'],
                                'skill' => ['skill_2323', 'skill_2324', 'skill_2325'],
                                'weapon' => ['wpn_2399'],
                                'accessory' => [null],
                            ],
                            'rewards' => [
                                'hair_2361_%s',
                                'set_2402_%s',
                                'set_2401_%s',
                                'back_2396',
                                'wpn_2399',
                                'pet_ancientgolem',
                                'skill_2323',
                                'skill_2324',
                                'skill_2325',
                                'emblem',
                                'tokens_45000',
                            ],
                        ],
                    ],
                ],
            ]
        ];
    }
}
