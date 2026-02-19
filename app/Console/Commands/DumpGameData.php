<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Log;

class DumpGameData extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'game:dump-data';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Downloads, decompresses, and saves Ninja Sage game data as JSON files.';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $assets = [
            "skills", "library", "enemy", "npc", "pet", "mission", 
            "gamedata", "talents", "senjutsu", "skill-effect", 
            "weapon-effect", "back_item-effect", "accessory-effect", 
            "arena-effect", "animation"
        ];

        $baseUrl = "https://ns-assets.ninjasage.id/static/lib/";
        $outputDir = "game_data";

        $this->info("Starting Ninja Sage Game Data Dump...");

        foreach ($assets as $asset) {
            $url = $baseUrl . $asset . ".bin";
            $this->output->write("Processing: <comment>{$asset}</comment> ... ");

            try {
                $response = Http::get($url);

                if (!$response->successful()) {
                    $this->error("FAILED (HTTP " . $response->status() . ")");
                    continue;
                }

                $compressedData = $response->body();
                
                // Try Zlib decompress (ActionScript Zlib standard)
                $jsonData = @gzuncompress($compressedData);

                if ($jsonData === false) {
                    // Fallback to Gzip decode
                    $jsonData = @gzdecode($compressedData);
                }

                if ($jsonData === false) {
                    $this->error("FAILED TO DECOMPRESS");
                    continue;
                }

                $fileName = "{$outputDir}/{$asset}.json";
                Storage::disk('local')->put($fileName, $jsonData);
                
                $this->info("SUCCESS -> storage/app/{$fileName}");

            } catch (\Exception $e) {
                $this->error("ERROR: " . $e->getMessage());
                Log::error("Game Data Dump Error ($asset): " . $e->getMessage());
            }
        }

        $this->info("\nDone! All available game data has been dumped to storage.");
        return 0;
    }
}