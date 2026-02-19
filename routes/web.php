<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AmfController;

Route::get('/', function () {
    return redirect('/playerdashboard');
});

// ✅ AMF Gateway Routes dengan Security Middleware
Route::middleware(['web'])->group(function () {
    Route::any('/amf', [AmfController::class, 'handle']);
    Route::any('/gateway.php', [AmfController::class, 'handle']);
    Route::post('/amf/admin-login', [AmfController::class, 'adminLogin']);
    Route::get('/amf/get-logs', [AmfController::class, 'getLogs']);
    Route::get('/amf/status', function() {
    return response()->json(['status' => 'active']);
});
});