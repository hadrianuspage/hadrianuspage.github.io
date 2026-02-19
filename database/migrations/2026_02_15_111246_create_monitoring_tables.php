<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // Cheat logs table - untuk tracking kecurangan
        Schema::create('cheat_logs', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('character_id')->nullable();
            $table->unsignedBigInteger('user_id')->nullable();
            $table->string('reason'); // Alasan cheat (item injection, token injection, dll)
            $table->string('ip_address')->nullable();
            $table->longText('data_sent')->nullable(); // Data yang dikirim client
            $table->longText('details')->nullable(); // Detail alasan cheat
            $table->string('target')->nullable(); // AMF target yang dicall
            $table->timestamps();
            
            // Indexes untuk query cepat
            $table->index('character_id');
            $table->index('user_id');
            $table->index('ip_address');
            $table->index('reason');
            $table->index('created_at');
            
            // Foreign keys
            $table->foreign('character_id')->references('id')->on('characters')->onDelete('cascade');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });

        // Login logs table - untuk monitoring login
        Schema::create('login_logs', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id')->nullable();
            $table->string('ip_address');
            $table->string('user_agent')->nullable();
            $table->boolean('success')->default(true);
            $table->string('reason')->nullable(); // Alasan jika gagal
            $table->timestamps();
            
            // Indexes
            $table->index('user_id');
            $table->index('ip_address');
            $table->index('created_at');
            
            // Foreign key
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });

        // Security events log - untuk tracking semua security events
        Schema::create('security_events', function (Blueprint $table) {
            $table->id();
            $table->string('event_type'); // PROXY_BLOCKED, RATE_LIMITED, OVERSIZED_PAYLOAD, dll
            $table->string('ip_address');
            $table->string('user_agent')->nullable();
            $table->longText('details')->nullable();
            $table->timestamps();
            
            // Indexes
            $table->index('event_type');
            $table->index('ip_address');
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('security_events');
        Schema::dropIfExists('login_logs');
        Schema::dropIfExists('cheat_logs');
    }
};