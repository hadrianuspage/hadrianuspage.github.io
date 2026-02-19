<?php

namespace App\Services\Amf;

use App\Services\Amf\Concerns\ValidatesSession;
use Illuminate\Support\Facades\Log;

class ExoticPackageService
{
    use ValidatesSession;

    /**
     * get
     * Params: [charId, sessionKey] (optional)
     */
    public function get($params = null)
    {
        if (is_array($params) && isset($params[0], $params[1])) {
            $guard = $this->guardCharacterSession((int)$params[0], $params[1]);
            if ($guard) {
                return $guard;
            }
        }

        Log::info('AMF ExoticPackage.get');

        return [
            'status' => 1,
            'error' => 0,
            'packages' => [],
        ];
    }
}
