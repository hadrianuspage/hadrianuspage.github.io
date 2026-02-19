<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::table('character_hunting_houses', function (Blueprint $table) {
            $table->text('current_bosses')->nullable()->after('last_daily_claim_date');
        });
    }

    public function down()
    {
        Schema::table('character_hunting_houses', function (Blueprint $table) {
            $table->dropColumn('current_bosses');
        });
    }
};

