<?php

namespace App\Services\Amf\FriendService;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use App\Models\GameConfig;
use App\Models\Item;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class ShopService
{
    use ValidatesSession;

    /**
     * getItems
     * Params: [charId, sessionKey]
     */
    public function getItems($charId, $sessionKey)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF FriendService.getItems: Char $charId");

        $char = Character::with('user')->find($charId);
        if (!$char) return ['status' => 0, 'result' => 'Character not found'];

        try {
            $catalog = $this->getDefaultCatalog();
            $ownedItems = $this->getOwnedItems($charId);
            $kunaiCount = $this->getKunaiCount($charId);
            
            // Check if user has emblem (account_type = 1)
            $hasEmblem = $char->user && $char->user->account_type >= 1;

            Log::info("AMF FriendService.getItems: Catalog loaded", [
                'char_id' => $charId,
                'catalog_count' => count($catalog),
                'kunai' => $kunaiCount,
                'has_emblem' => $hasEmblem
            ]);

            // Add ownership info to catalog
            $catalogWithOwnership = [];
            foreach ($catalog as $item) {
                $itemId = explode(':', $item['item'])[0];
                
                // Check ownership based on item type
                $owned = false;
                $quantity = 0;
                
                if (strtolower($itemId) === 'emblem') {
                    // Check emblem ownership
                    $owned = $hasEmblem;
                } elseif (str_starts_with($itemId, 'skill_')) {
                    // Check skill ownership
                    $owned = isset($ownedItems['skills'][$itemId]);
                } elseif (str_starts_with($itemId, 'tokens_') || 
                          str_starts_with($itemId, 'gold_') || 
                          str_starts_with($itemId, 'xp_') || 
                          str_starts_with($itemId, 'tp_')) {
                    // Currency - never show as owned
                    $owned = false;
                    $quantity = 0;
                } else {
                    // Equipment (wpn_, back_, set_, accessory_, hair_)
                    $owned = isset($ownedItems['items'][$itemId]);
                    $quantity = $ownedItems['items'][$itemId] ?? 0;
                }
                
                $catalogWithOwnership[] = [
                    'id' => $item['id'],
                    'item' => $item['item'],
                    'price' => $item['price'],
                    'owned' => $owned,
                    'quantity' => $quantity
                ];
            }

            return [
                'status' => 1,
                'items' => $catalogWithOwnership,
                'kunai' => $kunaiCount
            ];

        } catch (\Exception $e) {
            Log::error('AMF FriendService.getItems exception', [
                'char_id' => $charId,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            // Return safe fallback
            return [
                'status' => 1,
                'items' => $this->getDefaultCatalog(),
                'kunai' => 0
            ];
        }
    }

    /**
     * buyItem
     * Params: [charId, sessionKey, exchangeId]
     */
    public function buyItem($charId, $sessionKey, $exchangeId)
    {
        $guard = $this->guardCharacterSession((int)$charId, $sessionKey);
        if ($guard) {
            return $guard;
        }

        Log::info("AMF FriendService.buyItem: Char $charId Exchange $exchangeId");

        $char = Character::with('user')->find($charId);
        if (!$char) return ['status' => 0, 'result' => 'Character not found'];

        $catalog = collect($this->getDefaultCatalog())->keyBy('id');
        if (!$catalog->has($exchangeId)) {
            return ['status' => 2, 'result' => 'Item not found.'];
        }

        $entry = $catalog->get($exchangeId);
        $itemSpec = $entry['item'];
        $price = (int)$entry['price'];

        $itemParts = explode(':', $itemSpec);
        $itemId = $itemParts[0];

        // Check if trying to buy emblem but already has it
        if (strtolower($itemId) === 'emblem') {
            $hasEmblem = $char->user && $char->user->account_type >= 1;
            if ($hasEmblem) {
                return [
                    'status' => 2, 
                    'result' => 'Emblem already owned! You are already an Premium Member.'
                ];
            }
        }

        return DB::transaction(function () use ($charId, $itemId, $price, $itemSpec, $char) {
            $kunai = CharacterItem::lockForUpdate()
                ->where('character_id', $charId)
                ->where('item_id', FriendData::FRIENDSHIP_KUNAI)
                ->first();

            $currentKunai = $kunai ? (int)$kunai->quantity : 0;
            if ($currentKunai < $price) {
                return ['status' => 2, 'result' => 'Not enough Friendship Kunai.'];
            }

            // Deduct kunai
            if ($kunai) {
                $kunai->quantity = $currentKunai - $price;
                $kunai->save();
            }

            // Check if item is "emblem" - special handling
            if (strtolower($itemId) === 'emblem') {
                // Update account_type to 1 (Emblem Member)
                $user = $char->user;
                if ($user) {
                    $user->account_type = 1;
                    $user->save();
                    
                    Log::info('AMF FriendService.buyItem: Emblem activated', [
                        'char_id' => $charId,
                        'user_id' => $user->id,
                        'account_type' => 1
                    ]);
                }
                
                return [
                    'status' => 1,
                    'reward' => $itemSpec,
                    'kunai' => $kunai ? (int)$kunai->quantity : 0,
                    'result' => 'Emblem activated! You are now an Emblem Member!'
                ];
            }

            // Grant reward using RewardGrantService for normal items
            try {
                (new \App\Services\Amf\RewardGrantService())->grant($char, $itemSpec);
                
                Log::info('AMF FriendService.buyItem: Success', [
                    'char_id' => $charId,
                    'item' => $itemSpec,
                    'price' => $price,
                    'remaining_kunai' => $kunai ? (int)$kunai->quantity : 0
                ]);
            } catch (\Exception $e) {
                Log::error('Failed to grant friendship shop reward', [
                    'char_id' => $charId,
                    'item' => $itemSpec,
                    'error' => $e->getMessage()
                ]);
                throw $e;
            }

            return [
                'status' => 1,
                'reward' => $itemSpec,
                'kunai' => $kunai ? (int)$kunai->quantity : 0,
            ];
        });
    }

    private function getDefaultCatalog(): array
    {
        return [
            // Slot 1 - Skill
            [
                'id' => 0,
                'item' => 'skill_2140',
                'price' => 100
            ],
            // Slot 2 - Weapon
            [
                'id' => 1,
                'item' => 'wpn_2255',
                'price' => 50
            ],
            // Slot 3 - Back
            [
                'id' => 2,
                'item' => 'back_7014',
                'price' => 100
            ],
            // Slot 4 - Set (Male)
            [
                'id' => 3,
                'item' => 'set_7015_0',
                'price' => 15
            ],
            // Slot 5 - Skill
            [
                'id' => 4,
                'item' => 'skill_7003',
                'price' => 150
            ],
            // Slot 6 - Skill
            [
                'id' => 5,
                'item' => 'skill_7005',
                'price' => 150
            ],
            // Slot 7 - Tokens
            [
                'id' => 6,
                'item' => 'tokens_1000',
                'price' => 35
            ],
            // Slot 8 - Skill
            [
                'id' => 7,
                'item' => 'skill_673',
                'price' => 75
            ],
            // Slot 9 - TP
            [
                'id' => 8,
                'item' => 'tp_18000',
                'price' => 70
            ],
            // Slot 10 - Bebas (UBAH INI SESUKA HATI)
            // Bisa diganti dengan: weapon, skill, back, set, accessory, tokens, gold, tp, xp, emblem dll
            [
                'id' => 9,
                'item' => 'skill_701',
                'price' => 280
            ]
        ];
    }

    private function getOwnedItems(int $charId): array
    {
        // Get regular items
        $items = CharacterItem::where('character_id', $charId)
            ->pluck('quantity', 'item_id')
            ->toArray();
        
        // Get skills
        $skills = CharacterSkill::where('character_id', $charId)
            ->pluck('skill_id', 'skill_id')
            ->toArray();
            
        return [
            'items' => $items,
            'skills' => $skills
        ];
    }

    private function getKunaiCount(int $charId): int
    {
        $kunai = CharacterItem::where('character_id', $charId)
            ->where('item_id', FriendData::FRIENDSHIP_KUNAI)
            ->first();
            
        return $kunai ? (int)$kunai->quantity : 0;
    }

    private function grantSkill(int $charId, string $skillId): void
    {
        // Check if already owned
        $exists = CharacterSkill::where('character_id', $charId)
            ->where('skill_id', $skillId)
            ->exists();
            
        if (!$exists) {
            CharacterSkill::create([
                'character_id' => $charId,
                'skill_id' => $skillId,
                'level' => 1
            ]);
        }
    }

    private function grantEquipment(int $charId, string $itemId, int $quantity): void
    {
        $item = Item::where('item_id', $itemId)->first();
        $category = $item ? $item->category : 'item';

        $charItem = CharacterItem::where('character_id', $charId)
            ->where('item_id', $itemId)
            ->first();

        if ($charItem) {
            $charItem->quantity += $quantity;
            $charItem->save();
        } else {
            CharacterItem::create([
                'character_id' => $charId,
                'item_id' => $itemId,
                'quantity' => $quantity,
                'category' => $category,
            ]);
        }
    }

    private function grantItem(int $charId, string $itemId, int $quantity): void
    {
        $item = Item::where('item_id', $itemId)->first();
        $category = $item ? $item->category : 'item';

        $charItem = CharacterItem::where('character_id', $charId)
            ->where('item_id', $itemId)
            ->first();

        if ($charItem) {
            $charItem->quantity += $quantity;
            $charItem->save();
        } else {
            CharacterItem::create([
                'character_id' => $charId,
                'item_id' => $itemId,
                'quantity' => $quantity,
                'category' => $category,
            ]);
        }
    }
}