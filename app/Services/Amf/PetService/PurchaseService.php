<?php

namespace App\Services\Amf\PetService;

use App\Models\Character;
use App\Models\CharacterPet;
use App\Models\User;
use App\Models\Pet;
use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class PurchaseService
{
    use ValidatesSession;

    /**
     * Safe integer conversion
     */
    private function safeIntVal($value): int
    {
        if (is_null($value)) return 0;
        if (is_numeric($value)) return (int)$value;
        
        // Handle string numbers like "123" or "tokens_1"
        if (is_string($value)) {
            preg_match('/(\d+)/', $value, $matches);
            return isset($matches[1]) ? (int)$matches[1] : 0;
        }
        
        return 0;
    }

    /**
     * buyPet - dengan strict resource validation berdasarkan database structure
     */
    public function buyPet($params)
    {
        $guard = $this->guardCharacterSessionFromParams($params);
        if ($guard) {
            return $guard;
        }

        $charId = $params[0];
        $sessionKey = $params[1];
        $petId = $params[2];

        Log::info("AMF PetService.buyPet", [
            'char_id' => $charId,
            'pet_id_raw' => $petId,
            'session_key' => $sessionKey
        ]);

        try {
            return DB::transaction(function () use ($charId, $petId) {
                // ✅ Lock untuk mencegah race condition
                $char = Character::lockForUpdate()->find($charId);
                if (!$char) {
                    Log::error("buyPet: Character not found", ['char_id' => $charId]);
                    return ['status' => 0, 'error' => 'Character not found'];
                }

                $user = User::lockForUpdate()->find($char->user_id);
                if (!$user) {
                    Log::error("buyPet: User not found", ['user_id' => $char->user_id]);
                    return ['status' => 0, 'error' => 'User not found'];
                }

                // ✅ Smart pet_id cleaning
                $cleanPetId = str_replace('pet_', '', $petId);

                Log::info("buyPet: Looking for pet config", [
                    'original_pet_id' => $petId,
                    'clean_pet_id' => $cleanPetId
                ]);

                // ✅ Find pet config dari database
                $petConfig = Pet::where('pet_id', $cleanPetId)
                    ->orWhere('pet_id', $petId)
                    ->first();

                // ✅ Auto-create pet config jika tidak ada
                if (!$petConfig) {
                    Log::warning("buyPet: Pet config not found, creating default", [
                        'pet_id' => $cleanPetId
                    ]);

                    $petConfig = Pet::create([
                        'pet_id'        => $cleanPetId,
                        'name'          => ucfirst($cleanPetId),
                        'swf'           => $petId,
                        'price_gold'    => 10000,  // Default 10k gold
                        'price_tokens'  => 0,      // Default free
                        'premium'       => false,
                        'skills'        => null,   // Auto-detection
                        'icon'          => null
                    ]);

                    Log::info("buyPet: Created default pet config", $petConfig->only(['pet_id', 'name', 'price_gold', 'price_tokens']));
                }

                // ✅ Premium check
                if ($petConfig->premium && $user->account_type == 0) {
                    Log::info("buyPet: Premium pet requires membership", [
                        'pet_id' => $cleanPetId,
                        'user_account_type' => $user->account_type
                    ]);
                    return ['status' => 6]; // Triggers EmblemUpgrade popup
                }

                // ✅ STRICT RESOURCE VALIDATION berdasarkan database columns
                $priceGold     = $this->safeIntVal($petConfig->price_gold);
                $priceTokens   = $this->safeIntVal($petConfig->price_tokens);
                $currentGold   = $this->safeIntVal($char->gold);    // dari characters.gold
                $currentTokens = $this->safeIntVal($user->tokens);  // dari users.tokens

                Log::info("buyPet: Resource validation", [
                    'pet_config' => [
                        'price_gold_raw'   => $petConfig->price_gold,
                        'price_tokens_raw' => $petConfig->price_tokens,
                        'price_gold_safe'  => $priceGold,
                        'price_tokens_safe' => $priceTokens
                    ],
                    'user_resources' => [
                        'char_gold_raw'    => $char->gold,
                        'user_tokens_raw'  => $user->tokens,
                        'char_gold_safe'   => $currentGold,
                        'user_tokens_safe' => $currentTokens
                    ],
                    'validation' => [
                        'gold_required'   => $priceGold,
                        'gold_available'  => $currentGold,
                        'gold_sufficient' => $currentGold >= $priceGold,
                        'tokens_required'   => $priceTokens,
                        'tokens_available'  => $currentTokens,
                        'tokens_sufficient' => $currentTokens >= $priceTokens
                    ]
                ]);

                // ✅ STRICT Gold validation (characters.gold)
                if ($priceGold > 0) {
                    if ($currentGold < $priceGold) {
                        Log::warning("buyPet: INSUFFICIENT GOLD", [
                            'required' => $priceGold,
                            'available' => $currentGold,
                            'shortage' => $priceGold - $currentGold
                        ]);
                        return [
                            'status' => 3,
                            'result' => "Not enough Gold! Required: {$priceGold}, Available: {$currentGold}"
                        ];
                    }
                }

                // ✅ STRICT Tokens validation (users.tokens)
                if ($priceTokens > 0) {
                    if ($currentTokens < $priceTokens) {
                        Log::warning("buyPet: INSUFFICIENT TOKENS", [
                            'required' => $priceTokens,
                            'available' => $currentTokens,
                            'shortage' => $priceTokens - $currentTokens
                        ]);
                        return [
                            'status' => 3,
                            'result' => "Not enough Tokens! Required: {$priceTokens}, Available: {$currentTokens}"
                        ];
                    }
                }

                // ✅ DEDUCT RESOURCES - Strict database column updates
                $newGold = $currentGold;
                $newTokens = $currentTokens;

                // Deduct gold dari characters.gold
                if ($priceGold > 0) {
                    $newGold = $currentGold - $priceGold;
                    $char->update(['gold' => $newGold]);
                    
                    Log::info("buyPet: GOLD DEDUCTED", [
                        'char_id' => $charId,
                        'gold_before' => $currentGold,
                        'gold_spent' => $priceGold,
                        'gold_after' => $newGold
                    ]);
                }

                // Deduct tokens dari users.tokens
                if ($priceTokens > 0) {
                    $newTokens = $currentTokens - $priceTokens;
                    $user->update(['tokens' => $newTokens]);
                    
                    Log::info("buyPet: TOKENS DEDUCTED", [
                        'user_id' => $user->id,
                        'tokens_before' => $currentTokens,
                        'tokens_spent' => $priceTokens,
                        'tokens_after' => $newTokens
                    ]);
                }

                // ✅ CREATE PET INSTANCE di character_pets
                $newPet = CharacterPet::create([
                    'character_id' => $charId,
                    'pet_id'       => $petId, // Keep original format
                    'name'         => $petConfig->name,
                    'level'        => 1,
                    'xp'           => 0,
                    'created_at'   => now(),
                    'updated_at'   => now()
                ]);

                Log::info("buyPet: PET PURCHASE SUCCESS", [
                    'char_id'         => $charId,
                    'user_id'         => $user->id,
                    'pet_instance_id' => $newPet->id,
                    'pet_type_id'     => $petId,
                    'pet_name'        => $petConfig->name,
                    'transaction' => [
                        'gold_spent'    => $priceGold,
                        'tokens_spent'  => $priceTokens,
                        'gold_remaining'   => $newGold,
                        'tokens_remaining' => $newTokens
                    ]
                ]);

                return [
                    'status' => 1,
                    'error'  => 0,
                    'result' => "Successfully purchased: {$petConfig->name}!",
                    'data'   => [
                        'character_gold' => $newGold,    // Updated gold
                        'account_tokens' => $newTokens,   // Updated tokens
                        'pet_id'         => $newPet->id,
                        'pet_name'       => $petConfig->name,
                        'pet_level'      => 1
                    ]
                ];
            });

        } catch (\Exception $e) {
            Log::error("buyPet: EXCEPTION", [
                'char_id' => $charId,
                'pet_id'  => $petId,
                'error'   => $e->getMessage(),
                'file'    => $e->getFile(),
                'line'    => $e->getLine(),
                'trace'   => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 0, 
                'error' => 'Purchase failed: ' . $e->getMessage()
            ];
        }
    }

    /**
     * grantPet (Admin Developer Tools)
     */
    public function grantPet($params)
    {
        $guard = $this->guardCharacterSessionFromParams($params);
        if ($guard) {
            return $guard;
        }

        $charId = $params[0];
        $petId  = $params[2];

        Log::info("AMF PetService.grantPet", [
            'char_id'    => $charId,
            'pet_id_raw' => $petId
        ]);

        try {
            return DB::transaction(function () use ($charId, $petId) {
                $char = Character::lockForUpdate()->find($charId);
                if (!$char) {
                    Log::error("grantPet: Character not found", ['char_id' => $charId]);
                    return ['status' => 0, 'error' => 'Character not found'];
                }

                $user = User::lockForUpdate()->find($char->user_id);
                if (!$user) {
                    Log::error("grantPet: User not found", ['user_id' => $char->user_id]);
                    return ['status' => 0, 'error' => 'User not found'];
                }

                // ✅ Admin permission check (users.account_type)
                if (($user->account_type ?? 0) !== User::TYPE_ADMIN) {
                    Log::warning("grantPet: Permission denied", [
                        'user_id'      => $user->id,
                        'account_type' => $user->account_type
                    ]);
                    return ['status' => 0, 'error' => 'Admin privileges required'];
                }

                // ✅ Pet config handling
                $cleanPetId = str_replace('pet_', '', $petId);
                
                $petConfig = Pet::where('pet_id', $cleanPetId)
                    ->orWhere('pet_id', $petId)
                    ->first();

                if (!$petConfig) {
                    Log::info("grantPet: Creating pet config for grant", ['pet_id' => $cleanPetId]);
                    
                    $petConfig = Pet::create([
                        'pet_id'       => $cleanPetId,
                        'name'         => ucfirst($cleanPetId),
                        'swf'          => $petId,
                        'price_gold'   => 0,  // Free for grants
                        'price_tokens' => 0,
                        'premium'      => false,
                        'skills'       => null,
                        'icon'         => null
                    ]);
                }

                // ✅ Create pet instance (no cost deduction for grants)
                $newPet = CharacterPet::create([
                    'character_id' => $charId,
                    'pet_id'       => $petId,
                    'name'         => $petConfig->name,
                    'level'        => 1,
                    'xp'           => 0,
                    'created_at'   => now(),
                    'updated_at'   => now()
                ]);

                Log::info("grantPet: PET GRANTED SUCCESS", [
                    'admin_user_id'   => $user->id,
                    'target_char_id'  => $charId,
                    'pet_instance_id' => $newPet->id,
                    'pet_type_id'     => $petId,
                    'pet_name'        => $petConfig->name
                ]);

                return [
                    'status' => 1,
                    'result' => "Admin granted: {$petConfig->name}",
                    'data'   => [
                        'pet_id'   => $newPet->id,
                        'pet_name' => $petConfig->name
                    ]
                ];
            });
            
        } catch (\Exception $e) {
            Log::error("grantPet: EXCEPTION", [
                'char_id' => $charId,
                'pet_id'  => $petId,
                'error'   => $e->getMessage(),
                'trace'   => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 0, 
                'error' => 'Grant failed: ' . $e->getMessage()
            ];
        }
    }
}