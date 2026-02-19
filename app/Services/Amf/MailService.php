<?php

namespace App\Services\Amf;

use App\Services\Amf\MailService\ExecuteService;
use Illuminate\Support\Facades\Log;

class MailService
{
    private ExecuteService $executeService;

    public function __construct(ExecuteService $executeService = null)
    {
        $this->executeService = $executeService ?? new ExecuteService();
    }

    public function executeService($params)
    {
        try {
            return $this->executeService->executeService($params);
        } catch (\Throwable $e) {
            Log::error('MailService::executeService failed: ' . $e->getMessage(), ['exception' => $e, 'params' => $params]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function getMails($charId, $sessionKey)
    {
        try {
            return $this->executeService->getMails([$charId, $sessionKey]);
        } catch (\Throwable $e) {
            Log::error('MailService::getMails failed: '.$e->getMessage(), ['charId' => $charId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function openMail($charId, $sessionKey, $mailId)
    {
        try {
            return $this->executeService->openMail([$charId, $sessionKey, $mailId]);
        } catch (\Throwable $e) {
            Log::error('MailService::openMail failed: '.$e->getMessage(), ['charId' => $charId, 'mailId' => $mailId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function claimReward($charId, $sessionKey, $mailId)
    {
        try {
            return $this->executeService->claimReward([$charId, $sessionKey, $mailId]);
        } catch (\Throwable $e) {
            Log::error('MailService::claimReward failed: '.$e->getMessage(), ['charId' => $charId, 'mailId' => $mailId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function claimAllRewards($charId, $sessionKey)
    {
        try {
            return $this->executeService->claimAllRewards([$charId, $sessionKey]);
        } catch (\Throwable $e) {
            Log::error('MailService::claimAllRewards failed: '.$e->getMessage(), ['charId' => $charId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function deleteAllMails($charId, $sessionKey)
    {
        try {
            return $this->executeService->deleteAllMails([$charId, $sessionKey]);
        } catch (\Throwable $e) {
            Log::error('MailService::deleteAllMails failed: '.$e->getMessage(), ['charId' => $charId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }

    public function deleteMail($charId, $sessionKey, $mailId)
    {
        try {
            return $this->executeService->deleteMail([$charId, $sessionKey, $mailId]);
        } catch (\Throwable $e) {
            Log::error('MailService::deleteMail failed: '.$e->getMessage(), ['charId' => $charId, 'mailId' => $mailId]);
            return ['status' => 0, 'error' => 1, 'result' => 'Internal server error'];
        }
    }
}