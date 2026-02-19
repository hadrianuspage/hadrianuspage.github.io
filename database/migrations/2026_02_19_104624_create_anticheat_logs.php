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
        Schema::create('anticheat_logs', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('character_id')->nullable()->index();
            $table->json('detections');
            $table->string('user_agent', 255);
            $table->string('ip_address', 45);
            $table->boolean('is_critical')->default(false)->index();
            $table->timestamps();

            // Foreign key
            $table->foreign('character_id')
                ->references('id')
                ->on('characters')
                ->onDelete('set null');

            // Indexes
            $table->index(['created_at']);
            $table->index(['is_critical', 'created_at']);
            $table->index('ip_address');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('anticheat_logs');
    }
};
