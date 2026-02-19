<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\CharacterItem;
use App\Models\CharacterSkill;
use App\Models\User;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;

class CheatDetectionService
{
    /**
     * Validasi setiap request AMF - jika ada cheat langsung return cheating = true
     */
    public static function validateRequest(string $target, array $data): array
    {
        $data = array_filter($data); // Remove nulls

        // ======= 1. ITEM INJECTION CHECK =======
        if (self::hasItemInjection($data)) {
            return ['cheating' => true, 'reason' => 'Invalid item detected'];
        }

        // ======= 2. TOKEN INJECTION CHECK =======
        if (self::hasTokenInjection($data)) {
            return ['cheating' => true, 'reason' => 'Invalid token amount'];
        }

        // ======= 3. STAT MANIPULATION CHECK =======
        if (self::hasStatManipulation($data)) {
            return ['cheating' => true, 'reason' => 'Invalid character stats'];
        }

        // ======= 4. XP INJECTION CHECK =======
        if (self::hasXpInjection($data)) {
            return ['cheating' => true, 'reason' => 'Invalid XP amount'];
        }

        // ======= 5. LEVEL JUMP CHECK =======
        if (self::hasLevelJump($data)) {
            return ['cheating' => true, 'reason' => 'Invalid level progression'];
        }

        // ======= 6. HP/MP INJECTION CHECK =======
        if (self::hasHpMpInjection($data)) {
            return ['cheating' => true, 'reason' => 'Invalid HP/MP values'];
        }

        // ======= 7. SKILL INJECTION CHECK =======
        if (self::hasSkillInjection($data)) {
            return ['cheating' => true, 'reason' => 'Invalid skill detected'];
        }

        // ======= 8. QUANTITY MISMATCH CHECK =======
        if (self::hasQuantityMismatch($data)) {
            return ['cheating' => true, 'reason' => 'Item quantity mismatch'];
        }

        return ['cheating' => false, 'reason' => 'OK'];
    }

    /**
     * 1. Deteksi item yang tidak ada di database
     */
    private static function hasItemInjection(array $data): bool
    {
        if (empty($data['character_id']) || empty($data['item_id'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $itemId = $data['item_id'];

        $item = CharacterItem::where('character_id', $charId)
            ->where('item_id', $itemId)
            ->first();

        if (!$item) {
            Log::channel('security')->critical("CHEAT_ITEM_INJECTION - CharId: $charId - ItemId: $itemId");
            
            // ✅ LOG KE DATABASE
            $char = Character::find($charId);
            self::logCheat(
                $charId,
                $char?->user_id,
                'Item Injection',
                "Item tidak ada di database - ItemId: $itemId",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 2. Deteksi token yang invalid atau lebih dari yang dimiliki
     */
    private static function hasTokenInjection(array $data): bool
    {
        if (empty($data['user_id']) || !isset($data['tokens'])) {
            return false;
        }

        $userId = (int)$data['user_id'];
        $requestedTokens = (int)$data['tokens'];

        $user = User::find($userId);
        if (!$user) {
            Log::channel('security')->critical("CHEAT_TOKEN_USER_NOT_FOUND - UserId: $userId");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                null,
                $userId,
                'Token Injection',
                "User tidak ditemukan - UserId: $userId",
                $data
            );
            
            return true;
        }

        // Token tidak boleh negatif atau lebih dari yang dimiliki saat cheat spend
        if ($requestedTokens > $user->tokens || $requestedTokens < 0) {
            Log::channel('security')->critical("CHEAT_TOKEN_INJECTION - UserId: $userId - Requested: $requestedTokens - Have: {$user->tokens}");
            
            // ✅ LOG KE DATABASE
            $charId = $user->characters()->first()?->id;
            self::logCheat(
                $charId,
                $userId,
                'Token Injection',
                "Token inject - Requested: $requestedTokens, Have: {$user->tokens}",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 3. Deteksi stat yang ilegal (level > max, HP negatif, dll)
     */
    private static function hasStatManipulation(array $data): bool
    {
        if (empty($data['character_id'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $char = Character::find($charId);

        if (!$char) {
            return false;
        }

        // Level tidak boleh melebihi max untuk rank-nya
        $maxLevel = $char->getMaxLevel();
        if ($char->level > $maxLevel || $char->level < 1) {
            Log::channel('security')->critical("CHEAT_STAT_LEVEL - CharId: $charId - Level: {$char->level} - Max: $maxLevel");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'Stat Manipulation (Level)',
                "Level: {$char->level}, Max: $maxLevel",
                $data
            );
            
            return true;
        }

        // HP tidak boleh negatif atau melebihi max
        if ($char->hp < 0 || $char->hp > ($char->hp_max ?? 1000)) {
            Log::channel('security')->critical("CHEAT_STAT_HP - CharId: $charId - HP: {$char->hp}");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'Stat Manipulation (HP)',
                "HP: {$char->hp}, Max: {$char->hp_max}",
                $data
            );
            
            return true;
        }

        // MP tidak boleh negatif atau melebihi max
        if ($char->mp < 0 || $char->mp > ($char->mp_max ?? 1000)) {
            Log::channel('security')->critical("CHEAT_STAT_MP - CharId: $charId - MP: {$char->mp}");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'Stat Manipulation (MP)',
                "MP: {$char->mp}, Max: {$char->mp_max}",
                $data
            );
            
            return true;
        }

        // Rank tidak boleh invalid
        if ($char->rank < 0 || $char->rank > 10) {
            Log::channel('security')->critical("CHEAT_STAT_RANK - CharId: $charId - Rank: {$char->rank}");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'Stat Manipulation (Rank)',
                "Rank: {$char->rank}",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 4. Deteksi XP yang negatif atau tidak valid
     */
    private static function hasXpInjection(array $data): bool
    {
        if (empty($data['character_id'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $char = Character::find($charId);

        if (!$char) {
            return false;
        }

        // XP tidak boleh negatif
        if ($char->xp < 0) {
            Log::channel('security')->critical("CHEAT_XP_NEGATIVE - CharId: $charId - XP: {$char->xp}");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'XP Injection',
                "XP: {$char->xp} (negative)",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 5. Deteksi level jump (naik level without proper XP progression)
     */
    private static function hasLevelJump(array $data): bool
    {
        if (empty($data['character_id']) || empty($data['new_level'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $newLevel = (int)$data['new_level'];
        $char = Character::find($charId);

        if (!$char) {
            return false;
        }

        // Level tidak boleh naik lebih dari 1 per action (validasi dasar)
        // Atau lebih dari max level untuk rank-nya
        $maxLevel = $char->getMaxLevel();
        if ($newLevel > $maxLevel) {
            Log::channel('security')->critical("CHEAT_LEVEL_JUMP - CharId: $charId - NewLevel: $newLevel - Max: $maxLevel");
            
            // ✅ LOG KE DATABASE
            self::logCheat(
                $charId,
                $char->user_id,
                'Level Jump',
                "New Level: $newLevel, Max: $maxLevel",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 6. Deteksi HP/MP injection (nilai tidak sesuai dengan atribut)
     */
    private static function hasHpMpInjection(array $data): bool
    {
        if (empty($data['character_id']) || (empty($data['hp']) && empty($data['mp']))) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $char = Character::find($charId);

        if (!$char) {
            return false;
        }

        // HP check
        if (!empty($data['hp'])) {
            $hp = (int)$data['hp'];
            if ($hp > ($char->hp_max ?? 1000) || $hp < 0) {
                Log::channel('security')->critical("CHEAT_HP_INJECTION - CharId: $charId - HP: $hp - Max: {$char->hp_max}");
                
                // ✅ LOG KE DATABASE
                self::logCheat(
                    $charId,
                    $char->user_id,
                    'HP/MP Injection (HP)',
                    "HP: $hp, Max: {$char->hp_max}",
                    $data
                );
                
                return true;
            }
        }

        // MP check
        if (!empty($data['mp'])) {
            $mp = (int)$data['mp'];
            if ($mp > ($char->mp_max ?? 1000) || $mp < 0) {
                Log::channel('security')->critical("CHEAT_MP_INJECTION - CharId: $charId - MP: $mp - Max: {$char->mp_max}");
                
                // ✅ LOG KE DATABASE
                self::logCheat(
                    $charId,
                    $char->user_id,
                    'HP/MP Injection (MP)',
                    "MP: $mp, Max: {$char->mp_max}",
                    $data
                );
                
                return true;
            }
        }

        return false;
    }

    /**
     * 7. Deteksi skill yang tidak dimiliki character
     */
    private static function hasSkillInjection(array $data): bool
    {
        if (empty($data['character_id']) || empty($data['skill_id'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $skillId = $data['skill_id'];

        $skill = CharacterSkill::where('character_id', $charId)
            ->where('skill_id', $skillId)
            ->first();

        if (!$skill) {
            Log::channel('security')->critical("CHEAT_SKILL_INJECTION - CharId: $charId - SkillId: $skillId");
            
            // ✅ LOG KE DATABASE
            $char = Character::find($charId);
            self::logCheat(
                $charId,
                $char?->user_id,
                'Skill Injection',
                "Skill tidak ada - SkillId: $skillId",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * 8. Deteksi item quantity yang tidak sesuai dengan database
     */
    private static function hasQuantityMismatch(array $data): bool
    {
        if (empty($data['character_id']) || empty($data['item_id']) || !isset($data['quantity'])) {
            return false;
        }

        $charId = (int)$data['character_id'];
        $itemId = $data['item_id'];
        $requestedQty = (int)$data['quantity'];

        $item = CharacterItem::where('character_id', $charId)
            ->where('item_id', $itemId)
            ->first();

        if (!$item) {
            return true; // Item tidak ada
        }

        // Quantity tidak boleh lebih dari yang dimiliki saat action dilakukan
        if ($requestedQty > $item->quantity || $requestedQty < 0) {
            Log::channel('security')->critical("CHEAT_QUANTITY_MISMATCH - CharId: $charId - ItemId: $itemId - Requested: $requestedQty - Have: {$item->quantity}");
            
            // ✅ LOG KE DATABASE
            $char = Character::find($charId);
            self::logCheat(
                $charId,
                $char?->user_id,
                'Quantity Mismatch',
                "ItemId: $itemId, Requested: $requestedQty, Have: {$item->quantity}",
                $data
            );
            
            return true;
        }

        return false;
    }

    /**
     * Log cheat ke database dengan error handling
     */
    private static function logCheat(?int $charId, ?int $userId, string $reason, string $details, array $data): void
    {
        try {
            DB::table('cheat_logs')->insert([
                'character_id' => $charId,
                'user_id' => $userId,
                'reason' => $reason,
                'ip_address' => request()->ip(),
                'data_sent' => json_encode($data),
                'details' => $details,
                'target' => request()->header('X-AMF-Target', 'Unknown'),
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        } catch (\Exception $e) {
            Log::error("Failed to log cheat: " . $e->getMessage());
        }
    }
}