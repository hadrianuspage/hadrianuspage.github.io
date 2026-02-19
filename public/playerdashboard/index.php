<?php
require_once 'config.php';

$pdo = getDBConnection();
$error = '';
$success = '';

// Handle Logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: /playerdashboard');
    exit;
}

// Handle Login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $username = trim($_POST['username']);
    $password = $_POST['password'];
   
    $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
    $stmt->execute([$username]);
    $user = $stmt->fetch();
   
    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['id'];
        $_SESSION['username'] = $user['username'];
        header('Location: /playerdashboard');
        exit;
    } else {
        $error = 'Invalid username or password';
    }
}

// Check if user is logged in
$isLoggedIn = isset($_SESSION['user_id']);

if ($isLoggedIn) {
    // Get user data
    $stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch();
   
    // Get character data (current active character)
    $stmt = $pdo->prepare("SELECT * FROM characters WHERE user_id = ? ORDER BY id ASC LIMIT 1");
    $stmt->execute([$_SESSION['user_id']]);
    $character = $stmt->fetch();
   
    // Get all characters for this user
    $stmt = $pdo->prepare("SELECT id, name, level FROM characters WHERE user_id = ? ORDER BY id ASC");
    $stmt->execute([$_SESSION['user_id']]);
    $allCharacters = $stmt->fetchAll();
   
    // Handle AJAX requests
    if (isset($_POST['action'])) {
        header('Content-Type: application/json');
       
        switch ($_POST['action']) {
            case 'switch_character':
                $characterId = intval($_POST['character_id']);
               
                // Verify character belongs to user
                $stmt = $pdo->prepare("SELECT * FROM characters WHERE id = ? AND user_id = ?");
                $stmt->execute([$characterId, $_SESSION['user_id']]);
                $newChar = $stmt->fetch();
               
                if ($newChar) {
                    // Store the selected character ID in session
                    $_SESSION['selected_character_id'] = $characterId;
                   
                    echo json_encode([
                        'success' => true,
                        'message' => 'Character switched successfully!',
                        'character' => $newChar,
                        'reload' => true
                    ]);
                } else {
                    echo json_encode(['success' => false, 'message' => 'Invalid character selection.']);
                }
                exit;
               
            case 'update_email':
                $newEmail = trim($_POST['email']);
               
                // Update email
                $stmt = $pdo->prepare("UPDATE users SET email = ? WHERE id = ?");
                if ($stmt->execute([$newEmail, $_SESSION['user_id']])) {
                    echo json_encode(['success' => true, 'message' => 'Email updated successfully!', 'reload' => true]);
                } else {
                    echo json_encode(['success' => false, 'message' => 'Failed to update email.']);
                }
                exit;
               
            case 'update_password':
                $newPassword = $_POST['password'];
               
                // Update password
                $hashedPassword = password_hash($newPassword, PASSWORD_BCRYPT);
                $stmt = $pdo->prepare("UPDATE users SET password = ? WHERE id = ?");
                if ($stmt->execute([$hashedPassword, $_SESSION['user_id']])) {
                    echo json_encode(['success' => true, 'message' => 'Password updated successfully!', 'reload' => true]);
                } else {
                    echo json_encode(['success' => false, 'message' => 'Failed to update password.']);
                }
                exit;
               
            case 'delete_account':
                $stmt = $pdo->prepare("DELETE FROM users WHERE id = ?");
                if ($stmt->execute([$_SESSION['user_id']])) {
                    session_destroy();
                    echo json_encode(['success' => true, 'message' => 'Account deleted successfully!', 'redirect' => '/playerdashboard']);
                } else {
                    echo json_encode(['success' => false, 'message' => 'Failed to delete account.']);
                }
                exit;
               
            case 'change_username':
                $newUsername = trim($_POST['username']);
                $cost = 1000;
               
                if ($user['tokens'] < $cost) {
                    echo json_encode(['success' => false, 'message' => 'Insufficient tokens!']);
                    exit;
                }
               
                // Check if username exists
                $stmt = $pdo->prepare("SELECT id FROM users WHERE username = ? AND id != ?");
                $stmt->execute([$newUsername, $_SESSION['user_id']]);
                if ($stmt->fetch()) {
                    echo json_encode(['success' => false, 'message' => 'Username already taken!']);
                    exit;
                }
               
                $pdo->beginTransaction();
                try {
                    $stmt = $pdo->prepare("UPDATE users SET username = ?, tokens = tokens - ? WHERE id = ?");
                    $stmt->execute([$newUsername, $cost, $_SESSION['user_id']]);
                    $_SESSION['username'] = $newUsername;
                    $pdo->commit();
                    echo json_encode(['success' => true, 'message' => 'Username changed successfully!', 'new_tokens' => $user['tokens'] - $cost, 'reload' => true]);
                } catch (Exception $e) {
                    $pdo->rollBack();
                    echo json_encode(['success' => false, 'message' => 'Failed to change username.']);
                }
                exit;
               
            case 'change_account_type':
                $newType = intval($_POST['account_type']);
                $cost = 10000;
               
                if ($user['tokens'] < $cost) {
                    echo json_encode(['success' => false, 'message' => 'Insufficient tokens!']);
                    exit;
                }
               
                $stmt = $pdo->prepare("UPDATE users SET account_type = ?, tokens = tokens - ? WHERE id = ?");
                if ($stmt->execute([$newType, $cost, $_SESSION['user_id']])) {
                    echo json_encode(['success' => true, 'message' => 'Account type changed successfully!', 'new_tokens' => $user['tokens'] - $cost, 'reload' => true]);
                } else {
                    echo json_encode(['success' => false, 'message' => 'Failed to change account type.']);
                }
                exit;
               
            case 'change_gender':
                $newGender = intval($_POST['gender']);
                $cost = 5000;
               
                if ($user['tokens'] < $cost) {
                    echo json_encode(['success' => false, 'message' => 'Insufficient tokens!']);
                    exit;
                }
               
                $pdo->beginTransaction();
                try {
                    // Get current character ID
                    $currentCharId = isset($_SESSION['selected_character_id']) ? $_SESSION['selected_character_id'] : $character['id'];
                   
                    $stmt = $pdo->prepare("UPDATE characters SET gender = ? WHERE id = ? AND user_id = ?");
                    $stmt->execute([$newGender, $currentCharId, $_SESSION['user_id']]);
                   
                    $stmt = $pdo->prepare("UPDATE users SET tokens = tokens - ? WHERE id = ?");
                    $stmt->execute([$cost, $_SESSION['user_id']]);
                   
                    $pdo->commit();
                    echo json_encode(['success' => true, 'message' => 'Gender changed successfully!', 'new_tokens' => $user['tokens'] - $cost, 'reload' => true]);
                } catch (Exception $e) {
                    $pdo->rollBack();
                    echo json_encode(['success' => false, 'message' => 'Failed to change gender.']);
                }
                exit;
               
            case 'shop_buy':
    $itemType = $_POST['item_type'];
    $itemValue = $_POST['item_value'];
    $price = intval($_POST['price']);
    $priceType = $_POST['price_type'];
    $itemId = $_POST['item_id'] ?? '';
   
    // Security checks
    if ($itemId === 'welcome-3000') {
        $stmt = $pdo->prepare("SELECT created_at FROM user_claims WHERE user_id = ? AND claim_type = 'welcome_bonus' ORDER BY created_at DESC LIMIT 1");
        $stmt->execute([$_SESSION['user_id']]);
        $lastClaim = $stmt->fetch();
       
        if ($lastClaim) {
            $lastClaimTime = strtotime($lastClaim['created_at']);
            $now = time();
            $daysPassed = ($now - $lastClaimTime) / (60 * 60 * 24);
           
            $stmt = $pdo->prepare("SELECT claim_data FROM user_claims WHERE user_id = ? AND claim_type = 'welcome_bonus' ORDER BY created_at DESC LIMIT 1");
            $stmt->execute([$_SESSION['user_id']]);
            $claimData = $stmt->fetch();
           
            $requiredDays = 15;
            if ($claimData && $claimData['claim_data']) {
                $data = json_decode($claimData['claim_data'], true);
                $requiredDays = $data['required_days'] ?? 15;
            }
           
            if ($daysPassed < $requiredDays) {
                $remaining = ceil($requiredDays - $daysPassed);
                echo json_encode(['success' => false, 'message' => "You can claim this again in {$remaining} days"]);
                exit;
            }
        }
    }

    if ($itemId === 'chakra-ancestor-package') {
        if ($character['level'] < 20) {
            echo json_encode(['success' => false, 'message' => 'Required for Level 20! Your current level: ' . $character['level']]);
            exit;
        }
       
        $stmt = $pdo->prepare("SELECT id FROM user_claims WHERE user_id = ? AND claim_type = 'chakra_ancestor_package' LIMIT 1");
        $stmt->execute([$_SESSION['user_id']]);
        if ($stmt->fetch()) {
            echo json_encode(['success' => false, 'message' => 'You have already purchased this package!']);
            exit;
        }
    }

    if ($itemId === 'kinjutsu-kyubi-wrath') {
        if ($character['level'] < 60) {
            echo json_encode(['success' => false, 'message' => 'Required for Level 60! Your current level: ' . $character['level']]);
            exit;
        }
       
        $stmt = $pdo->prepare("SELECT id FROM user_claims WHERE user_id = ? AND claim_type = 'kinjutsu_kyubi_wrath' LIMIT 1");
        $stmt->execute([$_SESSION['user_id']]);
        if ($stmt->fetch()) {
            echo json_encode(['success' => false, 'message' => 'You have already purchased this skill!']);
            exit;
        }
    }

    if ($priceType === 'tokens') {
        if ($user['tokens'] < $price) {
            echo json_encode(['success' => false, 'message' => 'Insufficient tokens!']);
            exit;
        }
    } else {
        if ($character['gold'] < $price) {
            echo json_encode(['success' => false, 'message' => 'Insufficient gold!']);
            exit;
        }
    }

    $pdo->beginTransaction();
    try {
        $currentCharId = isset($_SESSION['selected_character_id']) ? $_SESSION['selected_character_id'] : $character['id'];

        if ($priceType === 'tokens') {
            $stmt = $pdo->prepare("UPDATE users SET tokens = tokens - ? WHERE id = ?");
            $stmt->execute([$price, $_SESSION['user_id']]);
        } else {
            $stmt = $pdo->prepare("UPDATE characters SET gold = gold - ? WHERE id = ? AND user_id = ?");
            $stmt->execute([$price, $currentCharId, $_SESSION['user_id']]);
        }

        switch ($itemType) {
            case 'tokens':
                $stmt = $pdo->prepare("UPDATE users SET tokens = tokens + ? WHERE id = ?");
                $stmt->execute([$itemValue, $_SESSION['user_id']]);
                break;

            case 'gold':
                $stmt = $pdo->prepare("UPDATE characters SET gold = gold + ? WHERE id = ? AND user_id = ?");
                $stmt->execute([$itemValue, $currentCharId, $_SESSION['user_id']]);
                break;

            case 'gear':
            case 'bundle':
                $items = explode(',', $itemValue);
                foreach ($items as $bundleItem) {
                    $bundleItem = trim($bundleItem);
                   
                    $category = 'item';
                    if (preg_match('/^wpn_/', $bundleItem)) {
                        $category = 'weapon';
                    } elseif (preg_match('/^back_/', $bundleItem)) {
                        $category = 'back';
                    } elseif (preg_match('/^set_/', $bundleItem)) {
                        $category = 'set';
                    } elseif (preg_match('/^accessory_/', $bundleItem)) {
                        $category = 'accessory';
                    } elseif (preg_match('/^hair_/', $bundleItem)) {
                        $category = 'hair';
                    }
                   
                    $stmt = $pdo->prepare("
                        INSERT INTO character_items (character_id, item_id, quantity, category, created_at, updated_at)
                        VALUES (?, ?, 1, ?, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE
                            quantity = quantity + 1,
                            updated_at = NOW()
                    ");
                    $stmt->execute([$currentCharId, $bundleItem, $category]);
                   
                    error_log("BUNDLE ITEM: character_id={$currentCharId}, item_id={$bundleItem}, category={$category}");
                }
                break;

            case 'skill':
                $stmt = $pdo->prepare("SELECT id FROM character_skills WHERE character_id = ? AND skill_id = ?");
                $stmt->execute([$currentCharId, $itemValue]);

                if (!$stmt->fetch()) {
                    $stmt = $pdo->prepare("INSERT INTO character_skills (character_id, skill_id, created_at, updated_at) VALUES (?, ?, NOW(), NOW())");
                    $stmt->execute([$currentCharId, $itemValue]);

                    error_log("SHOP SKILL BUY: character_id={$currentCharId}, skill_id={$itemValue}");
                } else {
                    error_log("SHOP SKILL SKIP: Skill already exists for character_id={$currentCharId}, skill_id={$itemValue}");
                }
                break;

            case 'pet':
                $stmt = $pdo->prepare("INSERT INTO character_pets (character_id, pet_id, level, xp, name, created_at, updated_at) VALUES (?, ?, 1, 0, '', NOW(), NOW())");
                $stmt->execute([$currentCharId, $itemValue]);
                break;

            case 'tp':
                $stmt = $pdo->prepare("UPDATE characters SET tp = tp + ? WHERE id = ? AND user_id = ?");
                $stmt->execute([$itemValue, $currentCharId, $_SESSION['user_id']]);
                break;
        }

        if ($itemId === 'welcome-3000') {
            $requiredDays = 15 + mt_rand(0, 15);
            $claimData = json_encode(['required_days' => $requiredDays]);
           
            $stmt = $pdo->prepare("INSERT INTO user_claims (user_id, claim_type, claim_data, created_at) VALUES (?, 'welcome_bonus', ?, NOW())");
            $stmt->execute([$_SESSION['user_id'], $claimData]);
        }

        if ($itemId === 'chakra-ancestor-package') {
            $stmt = $pdo->prepare("INSERT INTO user_claims (user_id, claim_type, claim_data, created_at) VALUES (?, 'chakra_ancestor_package', NULL, NOW())");
            $stmt->execute([$_SESSION['user_id']]);
        }

        if ($itemId === 'kinjutsu-kyubi-wrath') {
            $stmt = $pdo->prepare("INSERT INTO user_claims (user_id, claim_type, claim_data, created_at) VALUES (?, 'kinjutsu_kyubi_wrath', NULL, NOW())");
            $stmt->execute([$_SESSION['user_id']]);
        }

        $pdo->commit();
        echo json_encode(['success' => true, 'message' => 'Purchase successful!', 'reload' => true]);
    } catch (Exception $e) {
        $pdo->rollBack();
        error_log("SHOP BUY ERROR: " . $e->getMessage());
        echo json_encode(['success' => false, 'message' => 'Purchase failed: ' . $e->getMessage()]);
    }
    exit;

    case 'check_welcome_bonus':
        $stmt = $pdo->prepare("SELECT created_at, claim_data FROM user_claims WHERE user_id = ? AND claim_type = 'welcome_bonus' ORDER BY created_at DESC LIMIT 1");
        $stmt->execute([$_SESSION['user_id']]);
        $lastClaim = $stmt->fetch();
       
        if ($lastClaim) {
            $lastClaimTime = strtotime($lastClaim['created_at']);
            $now = time();
            $daysPassed = ($now - $lastClaimTime) / (60 * 60 * 24);
           
            $requiredDays = 15;
            if ($lastClaim['claim_data']) {
                $data = json_decode($lastClaim['claim_data'], true);
                $requiredDays = $data['required_days'] ?? 15;
            }
           
            if ($daysPassed < $requiredDays) {
                $remaining = ceil($requiredDays - $daysPassed);
                echo json_encode(['success' => false, 'message' => "You can claim this again in {$remaining} days"]);
                exit;
            }
        }
       
        echo json_encode(['success' => true, 'message' => 'Can claim welcome bonus']);
        exit;
   
            case 'redeem_code':
                $code = strtoupper(trim($_POST['code']));
               
                if (!preg_match('/^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/', $code)) {
                    echo json_encode(['success' => false, 'message' => 'Incorrect Format Redeem Codes']);
                    exit;
                }
               
                $configFile = __DIR__ . '/redeem_configs.json';
                if (!file_exists($configFile)) {
                    echo json_encode(['success' => false, 'message' => 'Redeem system unavailable.']);
                    exit;
                }
               
                $configs = json_decode(file_get_contents($configFile), true);
               
                if (!isset($configs[$code])) {
                    echo json_encode(['success' => false, 'message' => 'No redeem code found!']);
                    exit;
                }
               
                $redeemData = $configs[$code];
               
                $expiryDate = new DateTime($redeemData['expiry']);
                $now = new DateTime();
                if ($now > $expiryDate) {
                    echo json_encode(['success' => false, 'message' => 'This redeem code has expired.']);
                    exit;
                }
               
                if ($redeemData['claimed'] >= $redeemData['limit']) {
                    echo json_encode(['success' => false, 'message' => 'This redeem code has reached its claim limit.']);
                    exit;
                }
               
                if (in_array($user['username'], $redeemData['claimed_by'])) {
                    echo json_encode(['success' => false, 'message' => 'You have already claimed this code.']);
                    exit;
                }
               
                $pdo->beginTransaction();
                try {
                    $currentCharId = isset($_SESSION['selected_character_id']) ? $_SESSION['selected_character_id'] : $character['id'];
                   
                    foreach ($redeemData['rewards'] as $reward) {
                        if (preg_match('/^(tokens|gold|tp|xp)_(\d+)$/', $reward, $matches)) {
                            $type = $matches[1];
                            $value = intval($matches[2]);
                           
                            switch ($type) {
                                case 'tokens':
                                    $stmt = $pdo->prepare("UPDATE users SET tokens = tokens + ? WHERE id = ?");
                                    $stmt->execute([$value, $_SESSION['user_id']]);
                                    break;
                                case 'gold':
                                    $stmt = $pdo->prepare("UPDATE characters SET gold = gold + ? WHERE id = ? AND user_id = ?");
                                    $stmt->execute([$value, $currentCharId, $_SESSION['user_id']]);
                                    break;
                                case 'tp':
                                    $stmt = $pdo->prepare("UPDATE characters SET tp = tp + ? WHERE id = ? AND user_id = ?");
                                    $stmt->execute([$value, $currentCharId, $_SESSION['user_id']]);
                                    break;
                                case 'xp':
                                    $stmt = $pdo->prepare("UPDATE characters SET xp = xp + ? WHERE id = ? AND user_id = ?");
                                    $stmt->execute([$value, $currentCharId, $_SESSION['user_id']]);
                                    break;
                            }
                        } elseif (preg_match('/^(wpn|back|set|accessory|hair)_/', $reward)) {
                            $category = 'item';
                           
                            if (preg_match('/^wpn_/', $reward)) {
                                $category = 'weapon';
                            } elseif (preg_match('/^back_/', $reward)) {
                                $category = 'back';
                            } elseif (preg_match('/^set_/', $reward)) {
                                $category = 'set';
                            } elseif (preg_match('/^accessory_/', $reward)) {
                                $category = 'accessory';
                            } elseif (preg_match('/^hair_/', $reward)) {
                                $category = 'hair';
                            }
                           
                            $stmt = $pdo->prepare("
                                INSERT INTO character_items (character_id, item_id, quantity, category, created_at, updated_at)
                                VALUES (?, ?, 1, ?, NOW(), NOW())
                                ON DUPLICATE KEY UPDATE
                                    quantity = quantity + 1,
                                    updated_at = NOW()
                            ");
                            $stmt->execute([$currentCharId, $reward, $category]);
                           
                            error_log("REDEEM GEAR: character_id={$currentCharId}, item_id={$reward}, category={$category}");
                        } elseif (preg_match('/^skill_/', $reward)) {
                            $stmt = $pdo->prepare("SELECT id FROM character_skills WHERE character_id = ? AND skill_id = ?");
                            $stmt->execute([$currentCharId, $reward]);
                           
                            if (!$stmt->fetch()) {
                                $stmt = $pdo->prepare("INSERT INTO character_skills (character_id, skill_id, created_at, updated_at) VALUES (?, ?, NOW(), NOW())");
                                $stmt->execute([$currentCharId, $reward]);
                               
                                error_log("REDEEM SKILL: character_id={$currentCharId}, skill_id={$reward}");
                            } else {
                                error_log("REDEEM SKILL SKIP: Skill already exists for character_id={$currentCharId}, skill_id={$reward}");
                            }
                        }
                    }
                   
                    $configs[$code]['claimed']++;
                    $configs[$code]['claimed_by'][] = $user['username'];
                    file_put_contents($configFile, json_encode($configs, JSON_PRETTY_PRINT));
                   
                    $pdo->commit();
                    echo json_encode(['success' => true, 'message' => 'Redeem code claimed successfully!', 'reload' => true]);
                } catch (Exception $e) {
                    $pdo->rollBack();
                    error_log("REDEEM ERROR: " . $e->getMessage());
                    echo json_encode(['success' => false, 'message' => 'Failed to claim redeem code: ' . $e->getMessage()]);
                }
                exit;
               
            case 'afk_claim':
                $tokensReward = rand(1, 50);
                $goldReward = rand(1, 5000);
                $tpReward = rand(1, 500);
                $xpReward = rand(1, 10000);
               
                $pdo->beginTransaction();
                try {
                    $currentCharId = isset($_SESSION['selected_character_id']) ? $_SESSION['selected_character_id'] : $character['id'];
                   
                    $stmt = $pdo->prepare("UPDATE users SET tokens = tokens + ? WHERE id = ?");
                    $stmt->execute([$tokensReward, $_SESSION['user_id']]);
                   
                    $stmt = $pdo->prepare("UPDATE characters SET gold = gold + ?, tp = tp + ?, xp = xp + ? WHERE id = ? AND user_id = ?");
                    $stmt->execute([$goldReward, $tpReward, $xpReward, $currentCharId, $_SESSION['user_id']]);
                   
                    $pdo->commit();
                   
                    usleep(500000);
                   
                    echo json_encode([
                        'success' => true,
                        'rewards' => [
                            'tokens' => $tokensReward,
                            'gold' => $goldReward,
                            'tp' => $tpReward,
                            'xp' => $xpReward
                        ],
                        'message' => 'AFK rewards claimed successfully!'
                    ]);
                } catch (Exception $e) {
                    $pdo->rollBack();
                    echo json_encode(['success' => false, 'message' => 'Failed to claim AFK rewards.']);
                }
                exit;
               
            case 'get_character_details':
                $currentCharId = isset($_SESSION['selected_character_id']) ? $_SESSION['selected_character_id'] : $character['id'];
               
                $stmt = $pdo->prepare("SELECT * FROM characters WHERE id = ? AND user_id = ?");
                $stmt->execute([$currentCharId, $_SESSION['user_id']]);
                $currentChar = $stmt->fetch();
               
                echo json_encode(['success' => true, 'character' => $currentChar]);
                exit;
        }
    }
   
    if (isset($_SESSION['selected_character_id'])) {
        $stmt = $pdo->prepare("SELECT * FROM characters WHERE id = ? AND user_id = ?");
        $stmt->execute([$_SESSION['selected_character_id'], $_SESSION['user_id']]);
        $selectedChar = $stmt->fetch();
        if ($selectedChar) {
            $character = $selectedChar;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
       
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%);
            min-height: 100vh;
            color: #fff;
        }
       
        /* Login Page */
        .login-container {
            max-width: 450px;
            margin: 80px auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 50px 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
        }
       
        .login-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(30, 60, 114, 0.1), transparent);
            transform: rotate(45deg);
            animation: shimmer 3s infinite;
        }
       
        @keyframes shimmer {
            0% { transform: translateX(-100%) rotate(45deg); }
            100% { transform: translateX(100%) rotate(45deg); }
        }
       
        .login-container h2 {
            text-align: center;
            margin-bottom: 40px;
            color: #1e3c72;
            font-size: 32px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
       
        .login-welcome {
            text-align: center;
            color: #2a5298;
            margin-bottom: 30px;
            font-size: 16px;
            position: relative;
        }
       
        .form-group {
            margin-bottom: 25px;
            position: relative;
        }
       
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #1e3c72;
            font-weight: 600;
            font-size: 14px;
        }
       
        .form-group input {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #dae2f0;
            border-radius: 12px;
            font-size: 15px;
            transition: all 0.3s;
            background: #f8fafc;
        }
       
        .form-group input:focus {
            outline: none;
            border-color: #2a5298;
            background: white;
            box-shadow: 0 0 0 4px rgba(42, 82, 152, 0.1);
        }
       
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(30, 60, 114, 0.4);
            position: relative;
        }
       
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(30, 60, 114, 0.6);
        }
       
        .btn:active {
            transform: translateY(0);
        }
       
        .alert {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            font-size: 14px;
            position: relative;
        }
       
        .alert-error {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            border: none;
        }
       
        .alert-success {
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            color: white;
            border: none;
        }
       
        /* Dashboard */
        .dashboard-wrapper {
            display: flex;
            min-height: 100vh;
        }
       
        /* Hamburger Menu */
        .hamburger-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            border: none;
            border-radius: 12px;
            cursor: pointer;
            z-index: 1001;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 5px;
            transition: all 0.3s;
        }
       
        .hamburger-btn:hover {
            transform: scale(1.05);
        }
       
        .hamburger-btn span {
            width: 25px;
            height: 3px;
            background: white;
            border-radius: 3px;
            transition: all 0.3s;
        }
       
        .hamburger-btn.active span:nth-child(1) {
            transform: rotate(45deg) translate(7px, 7px);
        }
       
        .hamburger-btn.active span:nth-child(2) {
            opacity: 0;
        }
       
        .hamburger-btn.active span:nth-child(3) {
            transform: rotate(-45deg) translate(7px, -7px);
        }
       
        /* Sidebar Menu */
        .sidebar {
            position: fixed;
            left: -300px;
            top: 0;
            width: 280px;
            height: 100vh;
            background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
            box-shadow: 4px 0 20px rgba(0,0,0,0.3);
            transition: left 0.3s;
            z-index: 1000;
            padding: 90px 20px 20px;
            overflow-y: auto;
        }
       
        .sidebar.active {
            left: 0;
        }
       
        .menu-item {
            padding: 18px 20px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
       
        .menu-item:hover {
            background: rgba(255,255,255,0.2);
            transform: translateX(5px);
        }
       
        .menu-item.active {
            background: rgba(255,255,255,0.25);
        }
       
        /* Main Content */
        .main-content {
            flex: 1;
            padding: 20px;
            margin-left: 0;
            transition: margin-left 0.3s;
        }
       
        /* Dashboard Header */
        .dashboard-header {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
       
        .dashboard-header h1 {
            font-size: 28px;
            font-weight: 700;
        }
       
        .logout-btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
       
        .logout-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255, 107, 107, 0.6);
        }
       
        /* Card Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
       
        .card {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
            position: relative;
            transition: all 0.3s;
        }
       
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        }
       
        .card h3 {
            font-size: 22px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }
       
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
       
        .info-row:last-child {
            border-bottom: none;
        }
       
        .info-label {
            font-weight: 600;
            opacity: 0.9;
        }
       
        .info-value {
            font-weight: 600;
            color: #ffd700;
        }
       
        .change-account-btn {
            position: absolute;
            top: 25px;
            right: 25px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(81, 207, 102, 0.4);
        }
       
        .change-account-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(81, 207, 102, 0.6);
        }
       
        .character-dropdown {
            display: none;
            position: absolute;
            top: 70px;
            right: 25px;
            background: rgba(30, 60, 114, 0.98);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 100;
            min-width: 220px;
            overflow: hidden;
        }
       
        .character-dropdown.active {
            display: block;
        }
       
        .character-option {
            padding: 15px 20px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
       
        .character-option:last-child {
            border-bottom: none;
        }
       
        .character-option:hover {
            background: rgba(255,255,255,0.1);
        }
       
        .character-option.active {
            background: rgba(81, 207, 102, 0.3);
            font-weight: 600;
        }
       
        /* Modal Pages */
        .modal-page {
            display: none;
            padding: 20px;
        }
       
        .modal-page.active {
            display: block;
        }
       
        .modal-page h2 {
            font-size: 32px;
            margin-bottom: 30px;
            text-align: center;
        }
       
        .btn-small {
            padding: 12px 25px;
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 15px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(30, 60, 114, 0.4);
        }
       
        .btn-small:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(30, 60, 114, 0.6);
        }
       
        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
       
        .btn-danger:hover {
            box-shadow: 0 6px 25px rgba(255, 107, 107, 0.6);
        }
       
        /* Shop */
        .shop-categories {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 25px;
        }
       
        .category-btn {
            padding: 12px 24px;
            background: rgba(255,255,255,0.1);
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            color: white;
        }
       
        .category-btn.active {
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            border-color: #51cf66;
        }
       
        .shop-items {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
            max-height: 500px;
            overflow-y: auto;
            padding: 15px;
        }
       
        .shop-item {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid rgba(255,255,255,0.2);
            transition: all 0.3s;
        }
       
        .shop-item:hover {
            border-color: #51cf66;
            transform: translateY(-5px);
            box-shadow: 0 8px 32px rgba(81, 207, 102, 0.3);
        }
       
        .shop-item h4 {
            margin-bottom: 12px;
            font-size: 16px;
        }
       
        .shop-item .price {
            color: #ffd700;
            font-weight: 700;
            margin-bottom: 15px;
            font-size: 18px;
        }
       
        .shop-item button {
            width: 100%;
            padding: 10px;
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
       
        .shop-item button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(81, 207, 102, 0.6);
        }
       
        /* AFK Timer */
        .afk-timer {
            text-align: center;
            padding: 50px;
        }
       
        .timer-display {
            font-size: 72px;
            font-weight: bold;
            color: #ffd700;
            margin: 40px 0;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
        }
       
        .afk-rewards {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            border: 1px solid rgba(255,255,255,0.2);
        }
       
        .afk-rewards h4 {
            margin-bottom: 20px;
            font-size: 22px;
        }
       
        .reward-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 16px;
        }
       
        .reward-item:last-child {
            border-bottom: none;
        }
       
        .reward-item span:last-child {
            color: #ffd700;
            font-weight: 700;
        }
       
        /* AFK Minimized */
        .afk-minimized {
            display: none;
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            z-index: 999;
            cursor: pointer;
            border: 2px solid rgba(255,255,255,0.3);
            transition: all 0.3s;
        }
       
        .afk-minimized:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        }
       
        .afk-minimized.active {
            display: block;
        }
       
        .afk-minimized .timer-small {
            font-size: 28px;
            font-weight: bold;
            color: #ffd700;
        }
       
        .afk-minimized p {
            font-size: 13px;
            color: rgba(255,255,255,0.8);
            margin-top: 8px;
        }
       
        /* Toast */
        .toast {
            position: fixed;
            top: 25px;
            right: 25px;
            padding: 18px 30px;
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 2000;
            display: none;
            min-width: 300px;
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            font-weight: 600;
        }
       
        .toast.show {
            display: block;
            animation: slideIn 0.3s ease-out;
        }
       
        .toast.success {
            background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
        }
       
        .toast.error {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        }
       
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
       
        /* Responsive */
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
           
            .dashboard-header {
                flex-direction: column;
                gap: 20px;
                text-align: center;
            }
           
            .dashboard-header h1 {
                font-size: 22px;
            }
           
            .logout-btn {
                width: 100%;
            }
           
            .shop-items {
                grid-template-columns: 1fr;
            }
           
            .change-account-btn {
                position: static;
                display: block;
                margin-top: 15px;
                width: 100%;
            }
           
            .character-dropdown {
                position: static;
                margin-top: 10px;
            }
           
            .timer-display {
                font-size: 48px;
            }
        }

        /* Form Styling */
        .form-group {
            margin-bottom: 25px;
        }
       
        .form-group label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            font-size: 16px;
        }
       
        .form-group input, .form-group select {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 12px;
            font-size: 15px;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            color: white;
            transition: all 0.3s;
        }
       
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #51cf66;
            background: rgba(255,255,255,0.15);
            box-shadow: 0 0 0 4px rgba(81, 207, 102, 0.2);
        }
       
        .form-group input::placeholder {
            color: rgba(255,255,255,0.6);
        }
       
        /* Close Button */
        .close-btn {
            position: fixed;
            top: 25px;
            right: 25px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 24px;
            cursor: pointer;
            z-index: 1002;
            display: none;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
       
        .close-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(255, 107, 107, 0.6);
        }
       
        .close-btn.active {
            display: flex;
        }
       
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
       
        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }
       
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 4px;
        }
       
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5);
        }
    </style>
</head>
<body>
    <?php if (!$isLoggedIn): ?>
        <!-- Login Page -->
        <div class="login-container">
            <h2>Player Dashboard</h2>
            <div class="login-welcome">
                Welcome back! Please sign in to your account to access your player dashboard and manage your game progress.
            </div>
            <?php if ($error): ?>
                <div class="alert alert-error"><?php echo htmlspecialchars($error); ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required placeholder="Enter your username">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required placeholder="Enter your password">
                </div>
                <button type="submit" name="login" class="btn">Sign In</button>
            </form>
        </div>
    <?php else: ?>
        <!-- Dashboard -->
        <div class="dashboard-wrapper">
            <!-- Hamburger Button -->
            <button class="hamburger-btn" onclick="toggleMenu()">
                <span></span>
                <span></span>
                <span></span>
            </button>
           
            <!-- Close Button -->
            <button class="close-btn" onclick="showDashboard()">×</button>
           
            <!-- Sidebar Menu -->
            <div class="sidebar" id="sidebar">
                <div class="menu-item" onclick="showAccountProfile()">
                    <span>👤</span> Account Profile
                </div>
                <div class="menu-item" onclick="showChangeTokens()">
                    <span>🔄</span> Change with Tokens
                </div>
                <div class="menu-item" onclick="showShop()">
                    <span>🛒</span> Shop
                </div>
                <div class="menu-item" onclick="showRedeem()">
                    <span>🎫</span> Redeem Codes
                </div>
                <div class="menu-item" onclick="showAFK()">
                    <span>⏰</span> AFK
                </div>
            </div>
           
            <!-- Main Content -->
            <div class="main-content">
                <!-- Dashboard Page -->
                <div id="dashboard-page" class="modal-page active">
                    <div class="dashboard-header">
                        <h1>Hello. Welcome to Player Dashboard, <?php echo htmlspecialchars($user['username']); ?>!</h1>
                        <a href="?logout" class="logout-btn">Logout</a>
                    </div>
                   
                    <!-- Account Overview & Character -->
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>Account Overview</h3>
                            <div class="info-row">
                                <span class="info-label">Username:</span>
                                <span class="info-value"><?php echo htmlspecialchars($user['username']); ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Account Type:</span>
                                <span class="info-value"><?php echo $user['account_type'] == 1 ? 'Premium User' : 'Free User'; ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Gold:</span>
                                <span class="info-value" id="user-gold"><?php echo $character ? number_format($character['gold']) : '0'; ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Tokens:</span>
                                <span class="info-value" id="user-tokens"><?php echo number_format($user['tokens']); ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Registered:</span>
                                <span class="info-value"><?php echo date('Y-m-d H:i:s', strtotime($user['created_at'])); ?></span>
                            </div>
                        </div>
                       
                        <?php if ($character): ?>
                        <div class="card character-preview" onclick="showCharacterDetails()">
                            <button class="change-account-btn" onclick="event.stopPropagation(); toggleCharacterDropdown()">Change Account</button>
                            <div id="character-dropdown" class="character-dropdown">
                                <?php foreach ($allCharacters as $char): ?>
                                <div class="character-option <?php echo $char['id'] == $character['id'] ? 'active' : ''; ?>"
                                     onclick="event.stopPropagation(); switchCharacter(<?php echo $char['id']; ?>)">
                                    <?php echo htmlspecialchars($char['name']); ?> (Lv. <?php echo $char['level']; ?>)
                                </div>
                                <?php endforeach; ?>
                            </div>
                           
                            <h3>Your Character</h3>
                            <div class="info-row">
                                <span class="info-label">ID:</span>
                                <span class="info-value"><?php echo $character['id']; ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Name:</span>
                                <span class="info-value"><?php echo htmlspecialchars($character['name']); ?></span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Level:</span>
                                <span class="info-value"><?php echo $character['level']; ?></span>
                            </div>
                            <p style="text-align: center; margin-top: 15px; color: #ffd700; font-weight: 600;">Click to view full details</p>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
               
                <!-- Account Profile Page -->
                <div id="account-profile-page" class="modal-page">
                    <h2>Account Profile</h2>
                   
                    <div class="card">
                        <div class="info-row">
                            <span class="info-label">Username:</span>
                            <span class="info-value"><?php echo htmlspecialchars($user['username']); ?></span>
                        </div>
                       
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="new-email" value="<?php echo htmlspecialchars($user['email']); ?>">
                            <button class="btn-small" onclick="updateEmail()">Update Email</button>
                        </div>
                       
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="new-password" placeholder="Enter new password">
                            <button class="btn-small" onclick="updatePassword()">Update Password</button>
                        </div>
                       
                        <div class="form-group">
                            <button class="btn-small btn-danger" onclick="deleteAccount()">Delete Account</button>
                        </div>
                    </div>
                </div>
               
                <!-- Change with Tokens Page -->
                <div id="change-tokens-page" class="modal-page">
                    <h2>Change with Tokens</h2>
                   
                    <div class="card" style="margin-bottom: 30px;">
                        <div class="info-row">
                            <span class="info-label">Current Tokens:</span>
                            <span class="info-value" id="tokens-display"><?php echo number_format($user['tokens']); ?></span>
                        </div>
                    </div>
                   
                    <div class="card">
                        <div class="form-group">
                            <label>New Username (Cost: 1,000 tokens)</label>
                            <input type="text" id="new-username" placeholder="Enter new username">
                            <button class="btn-small" onclick="changeUsername()">Change Username</button>
                        </div>
                       
                        <div class="form-group">
                            <label>Account Type (Cost: 10,000 tokens)</label>
                            <select id="new-account-type">
                                <option value="0">Free User</option>
                                <option value="1">Premium User</option>
                            </select>
                            <button class="btn-small" onclick="changeAccountType()">Change Account Type</button>
                        </div>
                       
                        <div class="form-group">
                            <label>Gender (Cost: 5,000 tokens)</label>
                            <select id="new-gender">
                                <option value="0">Male</option>
                                <option value="1">Female</option>
                            </select>
                            <button class="btn-small" onclick="changeGender()">Change Gender</button>
                        </div>
                    </div>
                </div>
               
                <!-- Shop Page -->
                <div id="shop-page" class="modal-page">
                    <h2>Shop</h2>
                   
                    <div class="card" style="margin-bottom: 30px;">
                        <div class="info-row">
                            <span class="info-label">Account Type:</span>
                            <span class="info-value"><?php echo $user['account_type'] == 1 ? 'Premium User' : 'Free User'; ?></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Tokens:</span>
                            <span class="info-value" id="shop-tokens"><?php echo number_format($user['tokens']); ?></span>
                        </div>
                    </div>
                   
                    <div class="card">
                        <div class="shop-categories">
                            <button class="category-btn active" onclick="showShopCategory('welcome')">Welcome Bonus #2</button>
                            <button class="category-btn" onclick="showShopCategory('gold')">Gold</button>
                            <button class="category-btn" onclick="showShopCategory('gear')">Gear</button>
                            <button class="category-btn" onclick="showShopCategory('skills')">Skills</button>
                            <button class="category-btn" onclick="showShopCategory('pets')">Pets</button>
                            <button class="category-btn" onclick="showShopCategory('tp')">TP</button>
                        </div>
                       
                        <div id="shop-items-container" class="shop-items"></div>
                    </div>
                </div>
               
                <!-- Redeem Page -->
                <div id="redeem-page" class="modal-page">
                    <h2>Redeem Codes</h2>
                   
                    <div class="card">
                        <div class="form-group">
                            <label>Enter Redeem Code (Format: XXXX-XXXX-XXXX-XXXX)</label>
                            <input type="text" id="redeem-code" placeholder="XXXX-XXXX-XXXX-XXXX" maxlength="19" style="text-transform: uppercase;">
                            <button class="btn-small" onclick="redeemCode()">Redeem Now</button>
                        </div>
                    </div>
                </div>
               
                <!-- AFK Page -->
                <div id="afk-page" class="modal-page">
                    <h2>AFK Rewards</h2>
                   
                    <div class="card">
                        <div class="afk-timer">
                            <p style="font-size: 20px; margin-bottom: 20px;">Time Until Reward:</p>
                            <div class="timer-display" id="afk-timer">30:00</div>
                            <p style="color: rgba(255,255,255,0.8); font-size: 16px;">Stay on this page to keep AFK active</p>
                        </div>
                       
                        <div class="afk-rewards">
                            <h4>Total Rewards Earned:</h4>
                            <div class="reward-item">
                                <span>Tokens:</span>
                                <span id="afk-tokens-total">0</span>
                            </div>
                            <div class="reward-item">
                                <span>Gold:</span>
                                <span id="afk-gold-total">0</span>
                            </div>
                            <div class="reward-item">
                                <span>TP:</span>
                                <span id="afk-tp-total">0</span>
                            </div>
                            <div class="reward-item">
                                <span>XP:</span>
                                <span id="afk-xp-total">0</span>
                            </div>
                        </div>
                    </div>
                </div>
               
                <!-- Character Details Modal -->
                <div id="characterModal" class="modal-page">
                    <h2>Character Details</h2>
                    <div class="card">
                        <div id="characterDetailsContent"></div>
                    </div>
                </div>
            </div>
        </div>
       
        <!-- AFK Minimized -->
        <div id="afkMinimized" class="afk-minimized" onclick="showAFK()">
            <div class="timer-small" id="afk-timer-mini">30:00</div>
            <p>AFK Timer Running...</p>
        </div>
       
        <!-- Toast Notification -->
        <div id="toast" class="toast"></div>
       
        <script>
            // Global variables
            let afkTimerState = {
                interval: null,
                seconds: 0,
                totalRewards: { tokens: 0, gold: 0, tp: 0, xp: 0 },
                isMinimized: false,
                startTime: null
            };
           
            let currentPage = 'dashboard-page';
           
            // Menu Functions
            function toggleMenu() {
                const sidebar = document.getElementById('sidebar');
                const hamburger = document.querySelector('.hamburger-btn');
                const closeBtn = document.querySelector('.close-btn');
               
                sidebar.classList.toggle('active');
                hamburger.classList.toggle('active');
               
                if (sidebar.classList.contains('active')) {
                    closeBtn.classList.add('active');
                } else {
                    closeBtn.classList.remove('active');
                }
            }
           
            function showPage(pageId) {
                // Hide all pages
                document.querySelectorAll('.modal-page').forEach(page => {
                    page.classList.remove('active');
                });
               
                // Show selected page
                document.getElementById(pageId).classList.add('active');
                currentPage = pageId;
               
                // Close sidebar
                document.getElementById('sidebar').classList.remove('active');
                document.querySelector('.hamburger-btn').classList.remove('active');
                document.querySelector('.close-btn').classList.add('active');
               
                // Update menu active state
                document.querySelectorAll('.menu-item').forEach(item => {
                    item.classList.remove('active');
                });
            }
           
            function showDashboard() {
                showPage('dashboard-page');
                document.querySelector('.close-btn').classList.remove('active');
                
                // Stop AFK if going back to dashboard
                if (afkTimerState.interval && currentPage !== 'afk-page') {
                    stopAFKTimer();
                }
            }
           
            function showAccountProfile() {
                showPage('account-profile-page');
            }
           
            function showChangeTokens() {
                showPage('change-tokens-page');
            }
           
            function showShop() {
                showPage('shop-page');
                showShopCategory('welcome');
            }
           
            function showRedeem() {
                showPage('redeem-page');
            }
           
            function showAFK() {
                showPage('afk-page');
                startAFKTimer();
                document.getElementById('afkMinimized').classList.remove('active');
            }
           
            // Toast Notification
            function showToast(message, type = 'success') {
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.className = `toast ${type} show`;
                setTimeout(() => {
                    toast.classList.remove('show');
                }, 3000);
            }
           
            // AJAX Helper
            function ajaxRequest(action, data, callback) {
                const formData = new FormData();
                formData.append('action', action);
                for (let key in data) {
                    formData.append(key, data[key]);
                }
               
                fetch('', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(result => {
                    if (callback) callback(result);
                   
                    if (action === 'afk_claim') {
                        if (result.success && result.rewards) {
                            updateRewardsDisplay(result.rewards);
                        }
                        return;
                    }
                   
                    if (result.reload && action !== 'switch_character') {
                        if (afkTimerState.interval) {
                            saveAFKState();
                        }
                        setTimeout(() => location.reload(), 1500);
                    } else if (result.redirect) {
                        setTimeout(() => window.location.href = result.redirect, 2000);
                    }
                })
                .catch(error => {
                    console.error('AJAX Error:', error);
                    showToast('Request failed', 'error');
                });
            }
           
            // Character Functions
            function toggleCharacterDropdown() {
                const dropdown = document.getElementById('character-dropdown');
                dropdown.classList.toggle('active');
            }
           
            function switchCharacter(characterId) {
                ajaxRequest('switch_character', {character_id: characterId}, function(result) {
                    showToast(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        updateCharacterUI(result.character);
                        setTimeout(() => location.reload(), 1500);
                    }
                });
                toggleCharacterDropdown();
            }
           
            function updateCharacterUI(character) {
                const goldElement = document.getElementById('user-gold');
                if (goldElement && character.gold !== undefined) {
                    goldElement.textContent = Number(character.gold).toLocaleString();
                }
               
                const characterCard = document.querySelector('.character-preview');
                if (characterCard && character.name && character.level) {
                    const nameElement = characterCard.querySelector('.info-row:nth-child(3) .info-value');
                    const levelElement = characterCard.querySelector('.info-row:nth-child(4) .info-value');
                    const idElement = characterCard.querySelector('.info-row:nth-child(2) .info-value');
                   
                    if (nameElement) nameElement.textContent = character.name;
                    if (levelElement) levelElement.textContent = character.level;
                    if (idElement) idElement.textContent = character.id;
                }
            }
           
            function showCharacterDetails() {
                ajaxRequest('get_character_details', {}, function(result) {
                    if (result.success) {
                        const char = result.character;
                        let html = '';
                        const fields = [
                            {label: 'ID', value: char.id},
                            {label: 'Name', value: char.name},
                            {label: 'Level', value: char.level},
                            {label: 'XP', value: char.xp},
                            {label: 'Gender', value: char.gender == 0 ? 'Male' : 'Female'},
                            {label: 'Rank', value: char.rank},
                            {label: 'Class', value: char.class || 'N/A'},
                            {label: 'Gold', value: char.gold},
                            {label: 'TP', value: char.tp},
                            {label: 'Prestige', value: char.prestige},
                            {label: 'SS', value: char.ss},
                            {label: 'Element 1', value: char.element_1},
                            {label: 'Talent 1', value: char.talent_1 || 'N/A'},
                            {label: 'Talent 2', value: char.talent_2 || 'N/A'},
                            {label: 'Talent 3', value: char.talent_3 || 'N/A'},
                            {label: 'Weapon', value: char.equipment_weapon || 'N/A'},
                            {label: 'Back', value: char.equipment_back || 'N/A'},
                            {label: 'Clothing', value: char.equipment_clothing || 'N/A'},
                            {label: 'Accessory', value: char.equipment_accessory || 'N/A'},
                            {label: 'Skills', value: char.equipment_skills || 'N/A'},
                            {label: 'Pet', value: char.equipment_pet || 'N/A'},
                            {label: 'Point Wind', value: char.point_wind},
                            {label: 'Point Fire', value: char.point_fire},
                            {label: 'Point Lightning', value: char.point_lightning},
                            {label: 'Point Water', value: char.point_water},
                            {label: 'Point Earth', value: char.point_earth},
                            {label: 'Talent Skills', value: char.talent_skills || 'N/A'},
                            {label: 'Senjutsu Skills', value: char.senjutsu_skills || 'N/A'},
                            {label: 'Senjutsu Type', value: char.senjutsu_type || 'N/A'},
                            {label: 'Senjutsu Equipped Skills', value: char.senjutsu_equipped_skills || 'N/A'}
                        ];
                       
                        fields.forEach(field => {
                            html += `<div class="info-row">
                                <span class="info-label">${field.label}:</span>
                                <span class="info-value">${field.value}</span>
                            </div>`;
                        });
                       
                        document.getElementById('characterDetailsContent').innerHTML = html;
                        showPage('characterModal');
                    }
                });
            }
           
            // Account Profile Functions
            function updateEmail() {
                const email = document.getElementById('new-email').value;
                if (!email) {
                    showToast('Please enter an email address', 'error');
                    return;
                }
               
                ajaxRequest('update_email', {email: email}, function(result) {
                    showToast(result.message, result.success ? 'success' : 'error');
                });
            }
           
            function updatePassword() {
                const password = document.getElementById('new-password').value;
                if (!password || password.length < 6) {
                    showToast('Password must be at least 6 characters', 'error');
                    return;
                }
               
                ajaxRequest('update_password', {password: password}, function(result) {
                    showToast(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        document.getElementById('new-password').value = '';
                    }
                });
            }
           
            function deleteAccount() {
                if (confirm('WARNING: This action is irreversible! Are you sure you want to delete your account? All your data will be permanently lost.')) {
                    if (confirm('Final confirmation: Delete account permanently?')) {
                        ajaxRequest('delete_account', {}, function(result) {
                            showToast(result.message, result.success ? 'success' : 'error');
                        });
                    }
                }
            }
           
            // Change with Tokens Functions
            function changeUsername() {
                const username = document.getElementById('new-username').value;
                if (!username) {
                    showToast('Please enter a username', 'error');
                    return;
                }
               
                if (confirm('Change username for 1,000 tokens?')) {
                    ajaxRequest('change_username', {username: username}, function(result) {
                        showToast(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            updateTokensDisplay(result.new_tokens);
                        }
                    });
                }
            }
           
            function changeAccountType() {
                const accountType = document.getElementById('new-account-type').value;
               
                if (confirm('Change account type for 10,000 tokens?')) {
                    ajaxRequest('change_account_type', {account_type: accountType}, function(result) {
                        showToast(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            updateTokensDisplay(result.new_tokens);
                        }
                    });
                }
            }
           
            function changeGender() {
                const gender = document.getElementById('new-gender').value;
               
                if (confirm('Change gender for 5,000 tokens?')) {
                    ajaxRequest('change_gender', {gender: gender}, function(result) {
                        showToast(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            updateTokensDisplay(result.new_tokens);
                        }
                    });
                }
            }
           
            // Shop Functions
            function showShopCategory(category) {
                document.querySelectorAll('.category-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
               
                const container = document.getElementById('shop-items-container');
                let html = '';
               
                switch(category) {
                    case 'welcome':
                        html = generateShopItems([
                            {name: '3,000 Tokens', type: 'tokens', value: 3000, price: 0, priceType: 'free', button: 'Claim', id: 'welcome-3000'},
                            {name: '100 Tokens', type: 'tokens', value: 100, price: 500000, priceType: 'gold', button: 'Buy'},
                            {name: 'Chakra Ancestor Package', type: 'bundle', value: 'set_1155_0,back_605,wpn_1341', price: 0, priceType: 'free', button: 'Claim (Lvl 20+)', id: 'chakra-ancestor-package', description: 'Required for Level 20!'},
                            {name: 'Kinjutsu: Kyubi Wrath', type: 'skill', value: 'skill_2178', price: 0, priceType: 'free', button: 'Claim (Lvl 60+)', id: 'kinjutsu-kyubi-wrath', description: 'Required for Level 60!'}
                        ]);
                        break;
                       
                    case 'gold':
                        html = generateShopItems([
                            {name: '5,000 Gold', type: 'gold', value: 5000, price: 100, priceType: 'tokens', button: 'Buy'},
                            {name: '15,000 Gold', type: 'gold', value: 15000, price: 500, priceType: 'tokens', button: 'Buy'},
                            {name: '30,000 Gold', type: 'gold', value: 30000, price: 1000, priceType: 'tokens', button: 'Buy'},
                            {name: '50,000 Gold', type: 'gold', value: 50000, price: 2500, priceType: 'tokens', button: 'Buy'},
                            {name: '100,000 Gold', type: 'gold', value: 100000, price: 5000, priceType: 'tokens', button: 'Buy'},
                            {name: '500,000 Gold', type: 'gold', value: 500000, price: 10000, priceType: 'tokens', button: 'Buy'},
                            {name: '1,000,000 Gold', type: 'gold', value: 1000000, price: 30000, priceType: 'tokens', button: 'Buy'}
                        ]);
                        break;
                       
                    case 'gear':
                        html = generateShopItems([
                            {name: 'Ars Elemental Wand', type: 'gear', value: 'wpn_2399', price: 2200, priceType: 'tokens', button: 'Buy'},
                            {name: 'Ars Forbidden Grimoire', type: 'gear', value: 'back_2396', price: 1500, priceType: 'tokens', button: 'Buy'},
                            {name: 'Cursed Medallion', type: 'gear', value: 'accessory_2000', price: 800, priceType: 'tokens', button: 'Buy'},
                            {name: 'White Flakes', type: 'gear', value: 'back_2069', price: 800, priceType: 'tokens', button: 'Buy'},
                            {name: 'Ars Archmage Costume', type: 'gear', value: 'set_2401_0', price: 250, priceType: 'tokens', button: 'Buy'},
                            {name: 'Purple Magatama Keris', type: 'gear', value: 'wpn_2173', price: 600, priceType: 'tokens', button: 'Buy'}
                        ]);
                        break;
                       
                    case 'skills':
                        html = generateShopItems([
                            {name: 'Kinjutsu: Five Elements Consuming Seal', type: 'skill', value: 'skill_345', price: 600, priceType: 'tokens', button: 'Buy'},
                            {name: 'Full Turkey', type: 'skill', value: 'skill_518', price: 800, priceType: 'tokens', button: 'Buy'},
                            {name: 'Independence Renewal 1945', type: 'skill', value: 'skill_2031', price: 250, priceType: 'tokens', button: 'Buy'},
                            {name: 'Kinjutsu: Shark Water Pillar', type: 'skill', value: 'skill_2197', price: 100, priceType: 'tokens', button: 'Buy'},
                        ]);
                        break;
                       
                    case 'pets':
                        html = generateShopItems([
                            {name: 'Pet Syrup', type: 'pet', value: 'pet_syrup', price: 10000, priceType: 'tokens', button: 'Buy'},
                            {name: 'Pet Sanbi', type: 'pet', value: 'pet_sanbi', price: 3000, priceType: 'tokens', button: 'Buy'},
                            {name: 'Pet Nibi', type: 'pet', value: 'pet_nibi', price: 2000, priceType: 'tokens', button: 'Buy'},
                            
                        ]);
                        break;
                       
                    case 'tp':
                        const now = new Date();
                        const dayOfWeek = now.getDay();
                        const hour = now.getHours();
                       
                        let items = [
                            {name: '2,000 TP', type: 'tp', value: 2000, price: 4000, priceType: 'tokens', button: 'Buy'},
                            {name: '5,000 TP', type: 'tp', value: 5000, price: 8000, priceType: 'tokens', button: 'Buy'},
                            {name: '10,000 TP', type: 'tp', value: 10000, price: 12000, priceType: 'tokens', button: 'Buy'}
                        ];
                       
                        if (dayOfWeek >= 1 && dayOfWeek <= 5 && hour >= 7 && hour < 24) {
                            const seed = Math.floor(now.getTime() / (3 * 60 * 60 * 1000));
                            const rng = Math.sin(seed) * 10000;
                            const randomHour = 7 + Math.floor((rng - Math.floor(rng)) * 17);
                           
                            if (hour >= randomHour && hour < randomHour + 3) {
                                items.push({name: '17,500 TP (DISCOUNT!)', type: 'tp', value: 17500, price: 10500, priceType: 'tokens', button: 'Buy', special: true});
                            }
                        } else if (dayOfWeek === 0 || dayOfWeek === 6) {
                            showToast('News: TP Discount will be available on Monday, dont forget to visit!', 'error');
                        }
                       
                        html = generateShopItems(items);
                        break;
                }
               
                container.innerHTML = html;
            }
           
            function generateShopItems(items) {
                return items.map(item => {
                    const priceText = item.priceType === 'free' ? 'FREE' :
                                     item.priceType === 'tokens' ? `${item.price.toLocaleString()} Tokens` :
                                     `${item.price.toLocaleString()} Gold`;
                   
                    const specialClass = item.special ? 'style="border: 2px solid gold;"' : '';
                    const description = item.description ? `<p style="color: #ff6b6b; font-size: 12px; margin: 5px 0;">${item.description}</p>` : '';
                   
                    return `
                        <div class="shop-item" ${specialClass}>
                            <h4>${item.name}</h4>
                            ${description}
                            <div class="price">${priceText}</div>
                            <button onclick="buyItem('${item.type}', '${item.value}', ${item.price}, '${item.priceType}', '${item.id || ''}')">${item.button}</button>
                        </div>
                    `;
                }).join('');
            }
           
            function buyItem(type, value, price, priceType, itemId) {
                if (itemId === 'welcome-3000') {
                    ajaxRequest('check_welcome_bonus', {}, function(result) {
                        if (!result.success) {
                            showToast(result.message, 'error');
                            return;
                        }
                       
                        if (confirm('Claim this item?')) {
                            ajaxRequest('shop_buy', {
                                item_type: type,
                                item_value: value,
                                price: price,
                                price_type: priceType,
                                item_id: itemId
                            }, function(result) {
                                showToast(result.message, result.success ? 'success' : 'error');
                                if (result.success) {
                                    const requiredDays = 15 + Math.floor(Math.random() * 16);
                                    localStorage.setItem('welcome_bonus_claimed', 'true');
                                    localStorage.setItem('welcome_bonus_claim_time', Date.now().toString());
                                    localStorage.setItem('welcome_bonus_required_days', requiredDays.toString());
                                }
                            });
                        }
                    });
                    return;
                }

                const confirmMsg = priceType === 'free' ? 'Claim this item?' :
                                  priceType === 'tokens' ? `Buy for ${price.toLocaleString()} tokens?` :
                                  `Buy for ${price.toLocaleString()} gold?`;

                if (confirm(confirmMsg)) {
                    ajaxRequest('shop_buy', {
                        item_type: type,
                        item_value: value,
                        price: price,
                        price_type: priceType,
                        item_id: itemId || ''
                    }, function(result) {
                        showToast(result.message, result.success ? 'success' : 'error');
                    });
                }
            }
           
            // Redeem Functions
            function redeemCode() {
                let code = document.getElementById('redeem-code').value.toUpperCase().trim();
               
                code = code.replace(/[^A-Z0-9]/g, '');
                if (code.length > 16) code = code.substring(0, 16);
               
                const formatted = code.match(/.{1,4}/g);
                if (formatted) {
                    code = formatted.join('-');
                }
               
                if (!code.match(/^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/)) {
                    showToast('Incorrect Format Redeem Codes', 'error');
                    return;
                }
               
                ajaxRequest('redeem_code', {code: code}, function(result) {
                    showToast(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        document.getElementById('redeem-code').value = '';
                    }
                });
            }
           
            // AFK Functions
            function startAFKTimer() {
                if (afkTimerState.interval) return;
               
                afkTimerState.seconds = afkTimerState.seconds || 1800;
                afkTimerState.startTime = afkTimerState.startTime || Date.now();
                updateAFKDisplay();
               
                afkTimerState.interval = setInterval(() => {
                    afkTimerState.seconds--;
                    updateAFKDisplay();
                   
                    if (afkTimerState.seconds <= 0) {
                        claimAFKReward();
                        afkTimerState.seconds = 1800;
                        afkTimerState.startTime = Date.now();
                    }
                   
                    saveAFKState();
                }, 1000);
            }
           
            function stopAFKTimer() {
                if (afkTimerState.interval) {
                    clearInterval(afkTimerState.interval);
                    afkTimerState.interval = null;
                }
                clearAFKState();
                document.getElementById('afkMinimized').classList.remove('active');
            }
           
            function updateAFKDisplay() {
                const minutes = Math.floor(afkTimerState.seconds / 60);
                const seconds = afkTimerState.seconds % 60;
                const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
               
                const timer = document.getElementById('afk-timer');
                const timerMini = document.getElementById('afk-timer-mini');
               
                if (timer) timer.textContent = timeStr;
                if (timerMini) timerMini.textContent = timeStr;
            }
           
            function claimAFKReward() {
                ajaxRequest('afk_claim', {}, function(result) {
                    if (result.success) {
                        afkTimerState.totalRewards.tokens += result.rewards.tokens;
                        afkTimerState.totalRewards.gold += result.rewards.gold;
                        afkTimerState.totalRewards.tp += result.rewards.tp;
                        afkTimerState.totalRewards.xp += result.rewards.xp;
                       
                        document.getElementById('afk-tokens-total').textContent = afkTimerState.totalRewards.tokens.toLocaleString();
                        document.getElementById('afk-gold-total').textContent = afkTimerState.totalRewards.gold.toLocaleString();
                        document.getElementById('afk-tp-total').textContent = afkTimerState.totalRewards.tp.toLocaleString();
                        document.getElementById('afk-xp-total').textContent = afkTimerState.totalRewards.xp.toLocaleString();
                       
                        showToast(`AFK Reward: ${result.rewards.tokens} tokens, ${result.rewards.gold} gold, ${result.rewards.tp} TP, ${result.rewards.xp} XP`, 'success');
                        saveAFKState();
                       
                        updateRewardsDisplay(result.rewards);
                    }
                });
            }
           
            function updateRewardsDisplay(rewards) {
                const tokensElement = document.getElementById('user-tokens');
                const goldElement = document.getElementById('user-gold');
               
                if (tokensElement && rewards.tokens) {
                    const currentTokens = parseInt(tokensElement.textContent.replace(/,/g, ''));
                    const newTokens = currentTokens + rewards.tokens;
                    tokensElement.textContent = newTokens.toLocaleString();
                   
                    const tokensDisplay = document.getElementById('tokens-display');
                    const shopTokens = document.getElementById('shop-tokens');
                    if (tokensDisplay) tokensDisplay.textContent = newTokens.toLocaleString();
                    if (shopTokens) shopTokens.textContent = newTokens.toLocaleString();
                }
               
                if (goldElement && rewards.gold) {
                    const currentGold = parseInt(goldElement.textContent.replace(/,/g, ''));
                    const newGold = currentGold + rewards.gold;
                    goldElement.textContent = newGold.toLocaleString();
                }
            }
           
            // AFK State Management
            function saveAFKState() {
                if (afkTimerState.interval) {
                    const state = {
                        seconds: afkTimerState.seconds,
                        totalRewards: afkTimerState.totalRewards,
                        isMinimized: afkTimerState.isMinimized,
                        startTime: afkTimerState.startTime,
                        lastSave: Date.now()
                    };
                    localStorage.setItem('afkState', JSON.stringify(state));
                }
            }
           
            function restoreAFKState() {
                const savedState = localStorage.getItem('afkState');
                if (savedState) {
                    try {
                        const state = JSON.parse(savedState);
                        const timePassed = Math.floor((Date.now() - state.lastSave) / 1000);
                       
                        if (timePassed < 300) {
                            afkTimerState.seconds = Math.max(0, state.seconds - timePassed);
                            afkTimerState.totalRewards = state.totalRewards || { tokens: 0, gold: 0, tp: 0, xp: 0 };
                            afkTimerState.isMinimized = state.isMinimized;
                            afkTimerState.startTime = state.startTime;
                           
                            document.getElementById('afk-tokens-total').textContent = afkTimerState.totalRewards.tokens.toLocaleString();
                            document.getElementById('afk-gold-total').textContent = afkTimerState.totalRewards.gold.toLocaleString();
                            document.getElementById('afk-tp-total').textContent = afkTimerState.totalRewards.tp.toLocaleString();
                            document.getElementById('afk-xp-total').textContent = afkTimerState.totalRewards.xp.toLocaleString();
                           
                            if (state.isMinimized) {
                                document.getElementById('afkMinimized').classList.add('active');
                                startAFKTimer();
                            }
                        } else {
                            clearAFKState();
                        }
                    } catch (e) {
                        clearAFKState();
                    }
                }
            }
           
            function clearAFKState() {
                localStorage.removeItem('afkState');
                afkTimerState = {
                    interval: null,
                    seconds: 0,
                    totalRewards: { tokens: 0, gold: 0, tp: 0, xp: 0 },
                    isMinimized: false,
                    startTime: null
                };
            }
           
            function updateTokensDisplay(newTokens) {
                document.getElementById('user-tokens').textContent = newTokens.toLocaleString();
                const tokensDisplay = document.getElementById('tokens-display');
                const shopTokens = document.getElementById('shop-tokens');
                if (tokensDisplay) tokensDisplay.textContent = newTokens.toLocaleString();
                if (shopTokens) shopTokens.textContent = newTokens.toLocaleString();
            }
           
            // Event Listeners
            document.addEventListener('DOMContentLoaded', function() {
                const redeemInput = document.getElementById('redeem-code');
                if (redeemInput) {
                    redeemInput.addEventListener('input', function(e) {
                        let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
                        if (value.length > 16) value = value.substring(0, 16);
                       
                        const formatted = value.match(/.{1,4}/g);
                        e.target.value = formatted ? formatted.join('-') : value;
                    });
                }
               
                restoreAFKState();
            });
           
            // Close dropdown when clicking outside
            document.addEventListener('click', function(e) {
                const dropdown = document.getElementById('character-dropdown');
                const button = document.querySelector('.change-account-btn');
                if (dropdown && button && !dropdown.contains(e.target) && !button.contains(e.target)) {
                    dropdown.classList.remove('active');
                }
            });
           
            // Wake Lock for AFK
            let wakeLock = null;
            async function requestWakeLock() {
                try {
                    if ('wakeLock' in navigator) {
                        wakeLock = await navigator.wakeLock.request('screen');
                    }
                } catch (err) {
                    console.log('Wake Lock error:', err);
                }
            }
           
            // Request wake lock when AFK is active
            const observeAFK = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'class') {
                        const afkPage = document.getElementById('afk-page');
                        const afkMinimized = document.getElementById('afkMinimized');
                        const isAFKActive = afkPage.classList.contains('active') || afkMinimized.classList.contains('active');
                        if (isAFKActive) {
                            requestWakeLock();
                        } else if (wakeLock) {
                            wakeLock.release();
                            wakeLock = null;
                        }
                    }
                });
            });
           
            if (document.getElementById('afk-page') && document.getElementById('afkMinimized')) {
                observeAFK.observe(document.getElementById('afk-page'), { attributes: true });
                observeAFK.observe(document.getElementById('afkMinimized'), { attributes: true });
            }
        </script>
    <?php endif; ?>
</body>
</html>