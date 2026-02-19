<?php

namespace App\Services\Amf;

use Illuminate\Support\Facades\Log;

class RedeemTicketService
{
    protected RedeemTicket $impl;

    public function __construct(RedeemTicket $impl = null)
    {
        $this->impl = $impl ?? new RedeemTicket();
    }

    public function getData($params)
    {
        try {
            Log::info('AMF Service: RedeemTicketService.getData called', ['params' => $params]);
            return $this->impl->getData($params);
        } catch (\Throwable $e) {
            Log::error("AMF Service Error [RedeemTicket.getData]: " . $e->getMessage(), ['exception' => $e]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function exchange($params)
    {
        try {
            Log::info('AMF Service: RedeemTicketService.exchange called', ['params' => $params]);
            return $this->impl->exchange($params);
        } catch (\Throwable $e) {
            Log::error("AMF Service Error [RedeemTicket.exchange]: " . $e->getMessage(), ['exception' => $e]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function executeService($params)
    {
        try {
            Log::info('AMF Service: RedeemTicketService.executeService called', ['params' => $params]);

            if (is_array($params) && isset($params[0]) && is_array($params[0]) && isset($params[0][0])) {
                $command = $params[0][0];
                $args = $params[1] ?? [];
            } elseif (is_array($params) && isset($params[0]) && is_string($params[0])) {
                $command = $params[0];
                $args = $params[1] ?? [];
            } else {
                return $this->impl->getData($params);
            }

            switch ($command) {
                case 'getData':
                    return $this->impl->getData($args);
                case 'exchange':
                    return $this->impl->exchange($args);
                default:
                    Log::warning('RedeemTicketService.executeService unknown command', ['command' => $command]);
                    return ['status' => 0, 'error' => 1, 'result' => "Unknown command: {$command}"];
            }
        } catch (\Throwable $e) {
            Log::error("AMF Service Error [RedeemTicket.executeService]: " . $e->getMessage(), ['exception' => $e]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }
}
