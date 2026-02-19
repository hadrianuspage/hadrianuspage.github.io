<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\DB;

class SecurityMiddleware
{
    private const PROXY_SIGNATURES = [
        'charles', 'charles-proxy', 'burpsuite', 'proxy', 'fiddler'
    ];

    public function handle(Request $request, Closure $next)
    {
        // Allow localhost untuk dev (artisan serve)
        if (in_array($request->ip(), ['127.0.0.1', '::1'])) {
            return $next($request);
        }

        // ======= 1. DETECT PROXY/CHARLES =======
        $ua = strtolower($request->header('User-Agent', ''));
        $host = strtolower($request->header('Host', ''));
        
        foreach (self::PROXY_SIGNATURES as $signature) {
            if (str_contains($ua, $signature) || str_contains($host, $signature)) {
                Log::channel('security')->warning("PROXY_BLOCKED - IP: {$request->ip()} - UA: $ua");
                $this->logSecurityEvent('PROXY_BLOCKED', $request, "Proxy detected: $signature");
                return response('Access Denied', 403);
            }
        }

        // Check proxy ports
        if (in_array($request->getPort(), [8888, 8889, 8080, 9090, 9999, 3128])) {
            Log::channel('security')->warning("PROXY_PORT_BLOCKED - IP: {$request->ip()} - Port: {$request->getPort()}");
            $this->logSecurityEvent('PROXY_PORT_BLOCKED', $request, "Proxy port: {$request->getPort()}");
            return response('Access Denied', 403);
        }

        // ======= 2. DDOS RATE LIMITING =======
        $key = "rate_limit_{$request->ip()}";
        $count = Cache::get($key, 0);

        if ($count > 100) {
            Log::channel('security')->warning("RATE_LIMIT_EXCEEDED - IP: {$request->ip()} - Count: $count");
            $this->logSecurityEvent('RATE_LIMIT_EXCEEDED', $request, "Requests: $count/100");
            return response('Too Many Requests', 429);
        }

        Cache::put($key, $count + 1, 60);

        // ======= 3. PAYLOAD SIZE CHECK =======
        if (strlen($request->getContent()) > 512000) { // 512KB
            Log::channel('security')->critical("OVERSIZED_PAYLOAD - IP: {$request->ip()} - Size: " . strlen($request->getContent()));
            $this->logSecurityEvent('OVERSIZED_PAYLOAD', $request, "Size: " . strlen($request->getContent()) . " bytes");
            return response('Payload Too Large', 413);
        }

        return $next($request);
    }

    private function logSecurityEvent(string $eventType, Request $request, string $details): void
    {
        try {
            DB::table('security_events')->insert([
                'event_type' => $eventType,
                'ip_address' => $request->ip(),
                'user_agent' => $request->header('User-Agent'),
                'details' => $details,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        } catch (\Exception $e) {
            // Silent fail, jangan block kalau db error
            Log::error("Failed to log security event: " . $e->getMessage());
        }
    }
}