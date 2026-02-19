<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Cache;

class GenerateAdminCredentials extends Command
{
    protected $signature = 'admin:generate-credentials';
    protected $description = 'Generate admin credentials for logs access';

    public function handle()
    {
        $username = $this->generateRandomString(8);
        $password = $this->generateRandomString(12);

        Cache::put('admin_logs_credentials', [
            'username' => $username,
            'password' => $password
        ], 86400); // 24 hours

        $this->info('╔════════════════════════════════════════╗');
        $this->info('║   ADMIN LOGS CREDENTIALS GENERATED     ║');
        $this->info('╠════════════════════════════════════════╣');
        $this->line('║ Username: ' . str_pad($username, 28) . '║');
        $this->line('║ Password: ' . str_pad($password, 28) . '║');
        $this->info('╠════════════════════════════════════════╣');
        $this->warn('║  Valid for: 24 hours                   ║');
        $this->info('╚════════════════════════════════════════╝');

        return 0;
    }

    private function generateRandomString($length)
    {
        $characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        $result = '';
        for ($i = 0; $i < $length; $i++) {
            $result .= $characters[random_int(0, strlen($characters) - 1)];
        }
        return $result;
    }
}

