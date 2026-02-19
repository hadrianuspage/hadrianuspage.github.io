<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use SabreAMF_Message;
use SabreAMF_InputStream;
use SabreAMF_OutputStream;
use SabreAMF_Const;
use SabreAMF_AMF3_Wrapper;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use App\Models\Character;
use App\Models\User;
use App\Services\Amf\CheatDetectionService;
use Carbon\Carbon;

class AmfController extends Controller
{
    // ======= PERFORMANCE OPTIMIZATION =======
    private const CACHE_SESSION_TTL = 300; // 5 menit cache session
    private const SESSION_CACHE_KEY = 'amf_session_';
    private const CHARACTER_CACHE_KEY = 'amf_character_';

    /**
     * Handle the AMF Gateway request dengan optimasi performa
     */
    public function handle(Request $request)
    {
        // 1. Get the raw POST data
        $content = $request->getContent();

        if (empty($content)) {
            // ====== TAMPILAN GATEWAY PROFESIONAL ======
            return response()->view('amf.gateway', [], 200);
        }

        try {
            // 2. Deserialize the request
            $stream = new SabreAMF_InputStream($content);
            $amfRequest = new SabreAMF_Message();
            $amfRequest->deserialize($stream);
        } catch (\Exception $e) {
            Log::error("AMF Deserialization Error: " . $e->getMessage());
            return response('Invalid AMF Data', 500);
        }

        // 3. Prepare the Response Message
        $amfResponse = new SabreAMF_Message();
        $requestEncoding = $amfRequest->getEncoding();
        $useAmf3Wrapper = $requestEncoding === SabreAMF_Const::AMF3;
        $amfResponse->setEncoding($useAmf3Wrapper ? SabreAMF_Const::AMF0 : $requestEncoding);

        // 4. Process each "Body" dengan optimasi
        foreach ($amfRequest->getBodies() as $requestBody) {
            $responseBody = $this->handleBody($requestBody);
            if ($useAmf3Wrapper) {
                $responseBody['data'] = new SabreAMF_AMF3_Wrapper($this->normalizeAmf3Data($responseBody['data']));
            }

            $amfResponse->addBody($responseBody);
        }

        // 5. Serialize the response
        $outputStream = new SabreAMF_OutputStream();
        $amfResponse->serialize($outputStream);
        $output = $outputStream->getRawData();

        // 6. Return response dengan cache headers
        return response($output)
            ->header('Content-Type', 'application/x-amf')
            ->header('Cache-Control', 'no-cache, no-store, must-revalidate')
            ->header('Connection', 'Keep-Alive')
            ->header('Keep-Alive', 'timeout=5, max=100');
    }

    /**
     * Check Gateway Status
     */
    public function status()
    {
        try {
            // Simple health check
            $dbCheck = DB::connection()->getPdo();
            $cacheCheck = Cache::get('health_check', true);
            
            return response()->json([
                'status' => 'active',
                'timestamp' => now()->toISOString(),
                'database' => 'connected',
                'cache' => 'active'
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'status' => 'inactive',
                'timestamp' => now()->toISOString(),
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Admin Login untuk LOGS - Menggunakan Generated Credentials
     */
    public function adminLogin(Request $request)
    {
        $username = $request->input('username');
        $password = $request->input('password');

        // Ambil credentials dari cache yang di-generate oleh command
        $validCredentials = Cache::get('admin_logs_credentials');
        
        if (!$validCredentials) {
            return response()->json([
                'success' => false,
                'message' => 'No valid credentials found. Please run: php artisan admin:generate-credentials'
            ]);
        }

        if ($username === $validCredentials['username'] && $password === $validCredentials['password']) {
            $token = bin2hex(random_bytes(32));
            Cache::put('admin_logs_token_' . $token, true, 3600); // 1 hour session
            
            return response()->json([
                'success' => true,
                'token' => $token
            ]);
        }

        return response()->json([
            'success' => false,
            'message' => 'Invalid credentials'
        ]);
    }

    /**
     * Get Logs Data
     */
    public function getLogs(Request $request)
    {
        $token = $request->header('X-Admin-Token');
        
        if (!$token || !Cache::get('admin_logs_token_' . $token)) {
            return response()->json(['error' => 'Unauthorized'], 401);
        }

        $type = $request->input('type', 'registered');
        $limit = $request->input('limit', 100);
        $page = $request->input('page', 1);
        $offset = ($page - 1) * $limit;

        $logs = [];

        try {
            switch ($type) {
                case 'registered':
                    $logs = DB::table('users')
                        ->select('id', 'username', 'created_at')
                        ->orderBy('created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($user) {
                            return [
                                'type' => 'user_registration',
                                'id' => $user->id,
                                'username' => $user->username,
                                'detail' => "{$user->username} bergabung ke Mhantappu Saga!",
                                'timestamp' => $user->created_at
                            ];
                        });
                    break;

                case 'users':
                    $logs = DB::table('users')
                        ->select('id', 'name', 'username', 'email', 'account_type', 'tokens', 'created_at', 'updated_at')
                        ->orderBy('id', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($user) {
                            return [
                                'type' => 'user',
                                'id' => $user->id,
                                'name' => $user->name,
                                'username' => $user->username,
                                'email' => $user->email,
                                'account_type' => $user->account_type == 1 ? 'Premium' : 'Free',
                                'tokens' => $user->tokens,
                                'created_at' => $user->created_at,
                                'updated_at' => $user->updated_at
                            ];
                        });
                    break;

                case 'characters':
                    $logs = DB::table('characters')
                        ->join('users', 'characters.user_id', '=', 'users.id')
                        ->select('characters.id', 'characters.name', 'users.username', 'characters.level', 
                                 'characters.gold', 'characters.tp', 'characters.created_at', 'characters.updated_at')
                        ->orderBy('characters.id', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($char) {
                            return [
                                'type' => 'character',
                                'id' => $char->id,
                                'name' => $char->name,
                                'owner' => $char->username,
                                'level' => $char->level,
                                'gold' => $char->gold,
                                'tp' => $char->tp,
                                'created_at' => $char->created_at,
                                'updated_at' => $char->updated_at
                            ];
                        });
                    break;

                case 'skills':
                    $logs = DB::table('character_skills')
                        ->join('characters', 'character_skills.character_id', '=', 'characters.id')
                        ->join('users', 'characters.user_id', '=', 'users.id')
                        ->select('character_skills.*', 'characters.name as char_name', 'users.username')
                        ->orderBy('character_skills.created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($skill) {
                            return [
                                'type' => 'skill_purchase',
                                'character' => $skill->char_name,
                                'owner' => $skill->username,
                                'skill_id' => $skill->skill_id,
                                'action' => 'purchased',
                                'timestamp' => $skill->created_at
                            ];
                        });
                    break;

                case 'items':
                    $logs = DB::table('character_items')
                        ->join('characters', 'character_items.character_id', '=', 'characters.id')
                        ->join('users', 'characters.user_id', '=', 'users.id')
                        ->select('character_items.*', 'characters.name as char_name', 'users.username')
                        ->orderBy('character_items.created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($item) {
                            return [
                                'type' => 'item_purchase',
                                'character' => $item->char_name,
                                'owner' => $item->username,
                                'item_id' => $item->item_id,
                                'quantity' => $item->quantity,
                                'category' => $item->category ?? 'unknown',
                                'action' => 'purchased',
                                'timestamp' => $item->created_at
                            ];
                        });
                    break;

                case 'login_logs':
                    $logs = DB::table('login_logs')
                        ->leftJoin('users', 'login_logs.user_id', '=', 'users.id')
                        ->select('login_logs.*', 'users.username')
                        ->orderBy('login_logs.created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($log) {
                            return [
                                'type' => 'login_attempt',
                                'username' => $log->username ?? 'Unknown',
                                'ip_address' => $log->ip_address,
                                'success' => $log->success ? 'Yes' : 'No',
                                'reason' => $log->reason,
                                'timestamp' => $log->created_at
                            ];
                        });
                    break;

                case 'cheat_logs':
                    $logs = DB::table('cheat_logs')
                        ->leftJoin('characters', 'cheat_logs.character_id', '=', 'characters.id')
                        ->leftJoin('users', 'cheat_logs.user_id', '=', 'users.id')
                        ->select('cheat_logs.*', 'characters.name as char_name', 'users.username')
                        ->orderBy('cheat_logs.created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($log) {
                            return [
                                'type' => 'cheat_detected',
                                'character' => $log->char_name ?? 'N/A',
                                'username' => $log->username ?? 'N/A',
                                'reason' => $log->reason,
                                'ip_address' => $log->ip_address,
                                'target' => $log->target,
                                'timestamp' => $log->created_at,
                                'severity' => 'CRITICAL'
                            ];
                        });
                    break;

                case 'security_events':
                    $logs = DB::table('security_events')
                        ->orderBy('created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($event) {
                            return [
                                'type' => 'security_event',
                                'event_type' => $event->event_type,
                                'ip_address' => $event->ip_address,
                                'details' => $event->details,
                                'timestamp' => $event->created_at
                            ];
                        });
                    break;

                case 'pvp_battles':
                    $logs = DB::table('pvp_battles')
                        ->join('characters as host', 'pvp_battles.host_id', '=', 'host.id')
                        ->join('characters as enemy', 'pvp_battles.enemy_id', '=', 'enemy.id')
                        ->select('pvp_battles.*', 'host.name as host_name', 'enemy.name as enemy_name')
                        ->orderBy('pvp_battles.created_at', 'desc')
                        ->limit($limit)
                        ->offset($offset)
                        ->get()
                        ->map(function($battle) {
                            return [
                                'type' => 'pvp_battle',
                                'host' => $battle->host_name,
                                'enemy' => $battle->enemy_name,
                                'winner' => $battle->host_won ? $battle->host_name : $battle->enemy_name,
                                'mode' => $battle->mode,
                                'trophy_delta' => $battle->trophy_delta,
                                'timestamp' => $battle->created_at
                            ];
                        });
                    break;

                default:
                    return response()->json([
                        'success' => false,
                        'message' => 'Invalid log type'
                    ]);
            }
        } catch (\Exception $e) {
            Log::error("Error fetching logs: " . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Error fetching logs: ' . $e->getMessage()
            ], 500);
        }

        return response()->json([
            'success' => true,
            'logs' => $logs,
            'page' => $page,
            'limit' => $limit,
            'type' => $type
        ]);
    }

    private function handleBody($requestBody)
    {
        $target = $requestBody['target'] ?? '';
        $responseTarget = $requestBody['response'] ?? 'Unknown';
        $data = $requestBody['data'] ?? [];

        Log::info("AMF Call: $target");

        try {
            // ======= SESSION VALIDATION DENGAN CACHE =======
            $sessionError = $this->validateSessionKeyOptimized($target, $this->unwrapSingleArgArray($data));
            if ($sessionError) {
                return [
                    'target' => $responseTarget . '/onResult',
                    'response' => null,
                    'data' => $sessionError
                ];
            }

            // ======= CHEAT DETECTION - DISCONNECT IF CHEATING =======
            if (class_exists('App\Services\Amf\CheatDetectionService')) {
                $cheatStatus = CheatDetectionService::validateRequest($target, $data);
                if ($cheatStatus['cheating']) {
                    Log::critical("CHEAT_DETECTED - Target: $target - Reason: {$cheatStatus['reason']} - IP: " . request()->ip());
                    return [
                        'target' => $responseTarget . '/onStatus',
                        'response' => null,
                        'data' => [
                            'status' => 0,
                            'error' => 'Disconnected: ' . $cheatStatus['reason']
                        ]
                    ];
                }
            }

            // ======= DISPATCH SERVICE =======
            $result = $this->dispatchService($target, $data);

            return [
                'target'   => $responseTarget . '/onResult',
                'response' => null,
                'data'     => $result
            ];
        } catch (\Exception $e) {
            Log::error("AMF Service Error [$target]: " . $e->getMessage());

            return [
                'target'   => $responseTarget . '/onStatus',
                'response' => null,
                'data'     => [
                    'description' => $e->getMessage(),
                    'details'     => $e->getTraceAsString(),
                    'level'       => 'error',
                    'code'        => $e->getCode()
                ]
            ];
        }
    }

    /**
     * Session validation dengan cache untuk performa
     */
    private function validateSessionKeyOptimized(string $target, $data): ?array
{
    // ══════════ DISABLE SESSION VALIDATION ══════════
    // Tetap gunakan CheatDetectionService, tapi skip session validation
    return null;
    
    /*
    // ── Original session validation code (DISABLED for development) ──
    if (!is_array($data)) {
        return null;
    }

    $sessionKeyInfo = $this->extractSessionKeyInfo($data);
    if (!$sessionKeyInfo) {
        return null;
    }
    
    $sessionKey = $sessionKeyInfo['value'];

    // ======= CHECK CACHE DULU =======
    $cacheKey = self::SESSION_CACHE_KEY . $sessionKey;
    $cachedUser = Cache::get($cacheKey);
    
    if ($cachedUser) {
        // Validasi character ownership dari cache jika diperlukan
        if ($target === 'SystemLogin.getAllCharacters') {
            return null;
        }

        $numericIds = $this->extractNumericIds($data);
        if (empty($numericIds)) {
            return null;
        }

        // Cache character ownership check juga
        $charCacheKey = self::CHARACTER_CACHE_KEY . $cachedUser['id'] . '_' . implode('_', $numericIds);
        $cachedOwnership = Cache::get($charCacheKey);
        
        if ($cachedOwnership) {
            return null; // User owns character
        }
    }

    // ======= JIKA CACHE MISS, QUERY DATABASE =======
    $user = User::where('session_key', $sessionKey)
        ->select('id', 'username', 'session_key')
        ->first();

    if (!$user) {
        return ['status' => 0, 'error' => 'Invalid session key'];
    }

    // Cache user session untuk request berikutnya
    Cache::put($cacheKey, $user->toArray(), self::CACHE_SESSION_TTL);

    if ($target === 'SystemLogin.getAllCharacters') {
        return null;
    }

    $numericIds = $this->extractNumericIds($data);
    if (empty($numericIds)) {
        return null;
    }

    $ownsCharacter = Character::whereIn('id', $numericIds)
        ->where('user_id', $user->id)
        ->exists();

    if ($ownsCharacter) {
        // Cache ownership untuk request berikutnya
        $charCacheKey = self::CHARACTER_CACHE_KEY . $user->id . '_' . implode('_', $numericIds);
        Cache::put($charCacheKey, true, self::CACHE_SESSION_TTL);
        return null;
    }

    return ['status' => 0, 'error' => 'Invalid session key'];
    */
}



    private function dispatchService($target, $data)
    {
        $parts = explode('.', $target);
        $baseName = ucfirst($parts[0]);

        // If the AMF target name already ends with 'Service', don't add it again.
        if (str_ends_with($baseName, 'Service')) {
            $serviceName = $baseName;
        } else {
            $serviceName = $baseName . 'Service';
        }

        $methodName = $parts[1] ?? 'index';

        $fullClassName = "App\\Services\\Amf\\" . $serviceName;
        if (!class_exists($fullClassName)) {
            $fullClassName = "App\\Services\\" . $serviceName;

            if (!class_exists($fullClassName)) {
                throw new \Exception("Service '$serviceName' not found.");
            }
        }

        $serviceInstance = app($fullClassName);

        if (!method_exists($serviceInstance, $methodName)) {
            throw new \Exception("Method '$methodName' not found on service '$serviceName'.");
        }

        $method = new \ReflectionMethod($serviceInstance, $methodName);
        $args = $this->normalizeArgsForMethod($data, $method);

        return call_user_func_array([$serviceInstance, $methodName], $args);
    }

    private function extractSessionKeyInfo(array $data): ?array
    {
        foreach ($data as $index => $value) {
            if (is_string($value) && strlen($value) === 32) {
                return ['value' => $value, 'index' => $index];
            }
        }

        return null;
    }

    private function extractAdjacentNumericId(array $data, int $sessionIndex): ?int
    {
        $candidates = [];
        if (isset($data[$sessionIndex - 1])) {
            $candidates[] = $data[$sessionIndex - 1];
        }
        if (isset($data[$sessionIndex + 1])) {
            $candidates[] = $data[$sessionIndex + 1];
        }

        foreach ($candidates as $value) {
            if (is_numeric($value)) {
                $id = (int)$value;
                if ($id > 0) {
                    return $id;
                }
            }
        }

        return null;
    }

    private function extractNumericIds(array $data): array
    {
        $ids = [];
        foreach ($data as $value) {
            if (is_numeric($value)) {
                $id = (int)$value;
                if ($id > 0) {
                    $ids[] = $id;
                }
            }
        }

        return array_values(array_unique($ids));
    }

    private function normalizeArgsForMethod($data, \ReflectionMethod $method): array
    {
        if (!is_array($data)) {
            return [$data];
        }

        $paramCount = $method->getNumberOfParameters();

        if ($paramCount === 0) {
            return [];
        }

        if ($paramCount === 1) {
            if (array_is_list($data) && count($data) === 1) {
                return [$data[0]];
            }

            return [$data];
        }

        if (array_is_list($data) && count($data) === 1 && is_array($data[0])) {
            return $data[0];
        }

        return $data;
    }

    private function unwrapSingleArgArray($data)
    {
        if (is_array($data) && array_is_list($data) && count($data) === 1 && is_array($data[0])) {
            return $data[0];
        }

        return $data;
    }

    private function normalizeAmf3Data($data)
    {
        if (is_array($data)) {
            if (array_is_list($data)) {
                return array_map(function ($value) {
                    return $this->normalizeAmf3Data($value);
                }, $data);
            }

            $obj = new \stdClass();
            foreach ($data as $key => $value) {
                $obj->{$key} = $this->normalizeAmf3Data($value);
            }

            return $obj;
        }

        return $data;
    }
}