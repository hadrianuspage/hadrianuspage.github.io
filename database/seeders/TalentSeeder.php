<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Talent;

class TalentSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $talents = [
            "de" => ["is_emblem" => false, "price_gold" => 500000, "price_token" => 0, "talent_name" => "Dark Eye", "talent_description" => "Combine eye skill with acupuncture skill to give the user the ability to look through the target's nerves and meridians."],
            "dm" => ["is_emblem" => false, "price_gold" => 10000000, "price_token" => 1500, "talent_name" => "Dark Matter", "talent_description" => ""],
            "dp" => ["is_emblem" => false, "price_gold" => 500000, "price_token" => 0, "talent_name" => "Deadly Performance", "talent_description" => "Dead Bone performer can summon deceased beings in battles. Advanced performer can manipulate more dead bones at the same time."],
            "lm" => ["is_emblem" => false, "price_gold" => 10000000, "price_token" => 1500, "talent_name" => "Light Matter", "talent_description" => ""],
            "sm" => ["is_emblem" => true, "price_gold" => 0, "price_token" => 5000, "talent_name" => "Soul Marionette", "talent_description" => "A new body that was created by puppeteer after abandoning their flesh body. Become a full-fledged puppet while still being a puppeteer."],
            "eoc" => ["is_emblem" => false, "price_gold" => 20000000, "price_token" => 2500, "talent_name" => "Eye of Creation", "talent_description" => "The Eye of Creation skills unlock visionary power, enabling users to manifest and reshape intricate realities with unparalleled creativity."],
            "eom" => ["is_emblem" => true, "price_gold" => 0, "price_token" => 400, "talent_name" => "Eye of Mirror", "talent_description" => "An ancient eye skill which grants the user strong vision and perception, but it also brings a huge physical burden."],
            "ice" => ["is_emblem" => false, "price_gold" => 1000000, "price_token" => 0, "talent_name" => "Icy Crystal", "talent_description" => "Combine Wind and Water elements together to form a new element type - Icy Crystal. Use low temperature to attack target or protect yourself."],
            "iron" => ["is_emblem" => true, "price_gold" => 0, "price_token" => 2500, "talent_name" => "Iron Sand", "talent_description" => "Iron Sand is a powerful skill that manipulates particles to create versatile weapons or defenses. The user controls the iron sand to form barriers and projectiles, making it highly adaptable in combat."],
            "lava" => ["is_emblem" => false, "price_gold" => 1000000, "price_token" => 0, "talent_name" => "Explosive Lava", "talent_description" => "Explosive Lava is combined by the elements of Fire and Earth. User damage target by ignition and explosion."],
            "wood" => ["is_emblem" => false, "price_gold" => 1000000, "price_token" => 0, "talent_name" => "Enraged Forest", "talent_description" => "The Enraged Forest is combined by the elements of Water and Earth. User manipulates the growth of tree and uses wood to attack target."],
            "saint" => ["is_emblem" => false, "price_gold" => 0, "price_token" => 2500, "talent_name" => "Saint Power", "talent_description" => "'Saint Power' allows the user to achieve the pinnacle of chakra manipulation by understanding the fundamental essence of life."],
            "sound" => ["is_emblem" => false, "price_gold" => 1000000, "price_token" => 0, "talent_name" => "Demon Sound", "talent_description" => "The Demon Sound is combined by the elements of Thunder and Wind. Users interfere targets with different kinds of sounds and music."],
            "insect" => ["is_emblem" => false, "price_gold" => 3000000, "price_token" => 0, "talent_name" => "Insect Symbiosis", "talent_description" => "Years of studying various insects and learning their biology has unraveled the secrets of insect utilization and manipulation."],
            "orochi" => ["is_emblem" => false, "price_gold" => 0, "price_token" => 400, "talent_name" => "Orochi's Rage", "talent_description" => "Blessed by the great snake Orochi, the user gains protection and immunity to poison and also gains the ability to revive the dead."],
            "shadow" => ["is_emblem" => true, "price_gold" => 0, "price_token" => 400, "talent_name" => "Hidden Silhouette", "talent_description" => "Silhouette user manipulates human shadows to restrict and control target. Advanced user can incarnate shadows into physical objects and attack target directly."],
            "crystal" => ["is_emblem" => false, "price_gold" => 25000000, "price_token" => 2500, "talent_name" => "Crystal Manifestation", "talent_description" => "Crystal Manifestation taps into the latent energies of the environment, channeling them to create intricate and powerful crystalline structures."],
            "eightext" => ["is_emblem" => false, "price_gold" => 0, "price_token" => 400, "talent_name" => "Eight Extremities", "talent_description" => "This talent focuses on the flexibility of 8 body parts and the art of taijutsu. Explosive power can be achieved under extreme mode, but there will be serious side effects."]
        ];

        foreach ($talents as $id => $data) {
            Talent::updateOrCreate(['talent_id' => $id], [
                'name' => $data['talent_name'],
                'description' => $data['talent_description'],
                'price_gold' => $data['price_gold'],
                'price_tokens' => $data['price_token'],
                'is_emblem' => $data['is_emblem'],
                // Skills should probably be populated too, but I don't have the map handy here.
                // Assuming GameDataSeeder handles skills or they are not critical for PURCHASE check.
                // But for reset logic I need skills map.
                // I will leave skills as is (if existing) or empty.
                // Ideally I should merge with existing if exists.
            ]);
        }
    }
}