<?php

// Class untuk merepresentasikan karakter player
class Player {
    public $name;
    public $level;
    public $health;
    public $jutsus;

    public function __construct($name, $level) {
        $this->name = $name;
        $this->level = $level;
        $this->health = 100; // Inisialisasi health player
        $this->jutsus = []; // Inisialisasi array untuk menyimpan jutsu yang dimiliki player
    }

    public function addJutsu($jutsu) {
        $this->jutsus[] = $jutsu; // Menambahkan jutsu ke dalam array jutsus
    }

    public function attack($target) {
        // Logika serangan player terhadap target
        // ...
    }
}

// Class untuk merepresentasikan bangunan seperti academy
class Academy {
    public function teachJutsu($player, $jutsu) {
        $player->addJutsu($jutsu); // Menambahkan jutsu ke dalam array jutsus milik player
    }
}

// Class untuk merepresentasikan misi
class Mission {
    public function fight($player, $enemy) {
        // Logika pertarungan antara player dengan musuh
        // ...
    }
}

// Class untuk merepresentasikan hunting house
class HuntingHouse {
    public function fightMonster($player, $monster) {
        // Logika pertarungan antara player dengan monster
        // ...
    }
}

// Class untuk merepresentasikan event Halloween
class HalloweenEvent {
    public function fightSkeletonDemon($player, $demon) {
        // Logika pertarungan antara player dengan tengkorak iblis
        // ...
    }
}

// Membuat objek Player
$player = new Player("John", 1);

// Membuat objek Academy
$academy = new Academy();

// Menambahkan jutsu-jutsu ke dalam player menggunakan academy
$academy->teachJutsu($player, "Fiery Flame");
$academy->teachJutsu($player, "Lightning Impulse");
$academy->teachJutsu($player, "Wind Breaker");
$academy->teachJutsu($player, "Kage Bunshin no Jutsu");

// Membuat objek Mission
$mission = new Mission();

// Melawan musuh Shin
$mission->fight($player, "Shin");

// Melawan musuh Kojima
$mission->fight($player, "Kojima");

// Melawan musuh Naga Iblis
$mission->fight($player, "Naga Iblis");

// Membuat objek HuntingHouse
$huntingHouse = new HuntingHouse();

// Melawan monster Wherewolf
$huntingHouse->fightMonster($player, "Wherewolf");

// Membuat objek HalloweenEvent
$halloweenEvent = new HalloweenEvent();

// Melawan tengkorak iblis dalam event Halloween
$halloweenEvent->fightSkeletonDemon($player, "Tengkorak Iblis");

// Menampilkan gambar-gambar terkait game Ninja Saga
// ...

?>
