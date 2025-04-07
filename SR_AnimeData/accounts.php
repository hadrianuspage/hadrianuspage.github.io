
<?php
// Tentukan username dan password untuk otentikasi
$valid_username = "mhtpsg"; // Ganti dengan username Anda
$valid_password = "mhtpsg@2345"; // Ganti dengan password Anda

// Periksa apakah ada permintaan otentikasi
if (!isset($_SERVER['PHP_AUTH_USER']) ||
    $_SERVER['PHP_AUTH_USER'] !== $valid_username ||
    $_SERVER['PHP_AUTH_PW'] !== $valid_password) {
    header('WWW-Authenticate: Basic realm="My Realm"');
    header('HTTP/1.0 401 Unauthorized');
    echo 'Unauthorized';
    exit;
}

// Jika otentikasi berhasil, tampilkan data JSON
$data = [
    "accounts" => [
        [
            "username" => "Admin",
            "password" => "mhtpsg@loginmodmenupermanent"
        ],
        [
            "username" => "Guest",
            "password" => "guest"
        ]
    ]
];

header('Content-Type: application/json');
echo json_encode($data);
?>
