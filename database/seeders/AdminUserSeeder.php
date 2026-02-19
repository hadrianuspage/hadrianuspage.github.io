<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class AdminUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        \App\Models\User::updateOrCreate(
            ['email' => 'admin@ninjasage.test'],
            [
                'name' => 'Admin',
                'username' => 'admin',
                'password' => 'password', // Model casts to hashed
                'account_type' => \App\Models\User::TYPE_ADMIN,
                'email_verified_at' => now(),
            ]
        );
    }
}
