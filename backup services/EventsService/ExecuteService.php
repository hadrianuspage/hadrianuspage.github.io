<?php

namespace App\Services\Amf\EventsService;

use Illuminate\Support\Facades\Log;

class ExecuteService
{
    private CatalogService $catalogService;

    public function __construct()
    {
        $this->catalogService = new CatalogService();
    }

    /**
     * executeService
     */
    public function executeService($subService, $params)
    {
        Log::info("AMF EventsService.executeService: SubService $subService");

        if ($subService === 'get') {
            return $this->catalogService->get($params);
        }

        Log::error("EventsService: SubService $subService not implemented.");
        return ['status' => 0, 'error' => "SubService $subService not found"];
    }
}
