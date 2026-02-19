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
        Schema::create('character_thanksgiving_events', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('character_id')->unique();
            $table->integer('energy')->default(10);
            $table->integer('battles_count')->default(0);
            $table->date('last_battle_date')->nullable();
            $table->date('last_energy_reset')->nullable();
            $table->text('claimed_milestone_rewards')->nullable();
            $table->boolean('package_bought')->default(false);
            $table->timestamps();

            $table->foreign('character_id')
                ->references('id')
                ->on('characters')
                ->onDelete('cascade');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('character_thanksgiving_events');
    }
};

