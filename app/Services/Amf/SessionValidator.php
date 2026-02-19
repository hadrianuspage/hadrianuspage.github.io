<?php

namespace App\Services\Amf;

use App\Models\Character;
use App\Models\User;

class SessionValidator
{
    public static function validateCharacter(?int $charId, ?string $sessionKey): ?array
    {
        // ══════════ DISABLE SESSION VALIDATION ══════════
        // Langsung return null (artinya valid) untuk semua character validation
        return null;
        
        /*
        // ── Original validation code (DISABLED for development) ──
        if (!$charId || !$sessionKey) {
            return ['status' => 0, 'error' => 'Invalid session key'];
        }

        $char = Character::find($charId);
        if (!$char || !$char->user) {
            return ['status' => 0, 'error' => 'Character not found'];
        }

        if ($char->user->session_key !== $sessionKey) {
            return ['status' => 0, 'error' => 'Invalid session key'];
        }

        return null;
        */
    }

    public static function validateUser(?int $userId, ?string $sessionKey): ?array
    {
        // ══════════ DISABLE SESSION VALIDATION ══════════
        // Langsung return null (artinya valid) untuk semua user validation
        return null;
        
        /*
        // ── Original validation code (DISABLED for development) ──
        if (!$userId || !$sessionKey) {
            return ['status' => 0, 'error' => 'Invalid session key'];
        }

        $user = User::find($userId);
        if (!$user) {
            return ['status' => 0, 'error' => 'User not found'];
        }

        if ($user->session_key !== $sessionKey) {
            return ['status' => 0, 'error' => 'Invalid session key'];
        }

        return null;
        */
    }
}

