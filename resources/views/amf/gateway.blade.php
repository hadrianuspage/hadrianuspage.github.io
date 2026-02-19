<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>AMF Gateway</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f0f23;
            color: #e8e8e8;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            position: relative;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(90deg, rgba(255,107,107,0.03) 1px, transparent 1px),
                linear-gradient(rgba(255,107,107,0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            opacity: 0.3;
        }

        .container {
            text-align: center;
            z-index: 1;
            max-width: 650px;
            width: 100%;
        }

        .gateway-card {
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            border-radius: 12px;
            padding: 50px 35px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        .ninja-icon {
            font-size: 4em;
            margin-bottom: 25px;
            filter: drop-shadow(0 0 20px rgba(255, 107, 107, 0.4));
        }

        h1 {
            font-size: 2em;
            color: #ffffff;
            margin-bottom: 12px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        .question {
            font-size: 1.1em;
            color: #9b9baa;
            margin-bottom: 30px;
            font-weight: 400;
        }

        .server-name {
            display: inline-block;
            color: #ff6b6b;
            font-weight: 600;
            font-size: 1em;
            padding: 8px 18px;
            background: rgba(255, 107, 107, 0.08);
            border: 1px solid rgba(255, 107, 107, 0.2);
            border-radius: 6px;
            margin-top: 5px;
        }

        .footer-info {
            position: fixed;
            top: 18px;
            left: 18px;
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 0.85em;
            color: #9b9baa;
            max-width: 280px;
            z-index: 10;
        }

        .footer-info a {
            color: #ff6b6b;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }

        .footer-info a:hover {
            color: #ff8787;
        }

        /* Header Controls */
        .header-controls {
            position: fixed;
            top: 18px;
            right: 18px;
            display: flex;
            gap: 12px;
            z-index: 10;
            align-items: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 0.88em;
            font-weight: 600;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            position: relative;
        }

        .status-dot.connected {
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }

        .status-dot.connected::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: #10b981;
            animation: pulse-dot 2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(1.5);
                opacity: 0;
            }
        }

        .status-dot.disconnected {
            background: #ef4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
        }

        .status-dot.reconnecting {
            background: #f59e0b;
            box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
            animation: blink 1s ease-in-out infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .status-text {
            color: #e8e8e8;
        }

        .status-text.connected {
            color: #10b981;
        }

        .status-text.disconnected {
            color: #ef4444;
        }

        .status-text.reconnecting {
            color: #f59e0b;
        }

        .logs-button {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.25);
            transition: all 0.2s;
        }

        .logs-button:hover {
            background: #ff5252;
            box-shadow: 0 6px 16px rgba(255, 107, 107, 0.35);
            transform: translateY(-1px);
        }

        /* Modal Base */
        .overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            z-index: 1000;
            backdrop-filter: blur(4px);
        }

        .overlay.show {
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .modal-box {
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            width: 90%;
            max-width: 420px;
            border-radius: 12px;
            padding: 35px;
            position: relative;
        }

        .close-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            background: transparent;
            border: none;
            color: #9b9baa;
            font-size: 1.8em;
            cursor: pointer;
            width: 35px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.2s;
        }

        .close-btn:hover {
            color: #ff6b6b;
        }

        .modal-box h2 {
            margin-bottom: 8px;
            color: #ffffff;
            font-size: 1.5em;
            font-weight: 600;
        }

        .warning-badge {
            background: #ff6b6b;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            margin-bottom: 25px;
            font-weight: 600;
            font-size: 0.9em;
            display: inline-block;
        }

        .form-field {
            margin-bottom: 18px;
            text-align: left;
        }

        .form-field label {
            display: block;
            margin-bottom: 7px;
            color: #c8c8d0;
            font-weight: 500;
            font-size: 0.9em;
        }

        .form-field input {
            width: 100%;
            padding: 11px 14px;
            background: #0f0f23;
            border: 1px solid #2a2a40;
            border-radius: 7px;
            font-size: 0.95em;
            color: #ffffff;
            transition: border 0.2s;
        }

        .form-field input:focus {
            outline: none;
            border-color: #ff6b6b;
        }

        .submit-btn {
            width: 100%;
            padding: 13px;
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 7px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 8px;
        }

        .submit-btn:hover {
            background: #ff5252;
        }

        .error-msg {
            color: #ff6b6b;
            margin-top: 12px;
            font-size: 0.9em;
            font-weight: 500;
        }

        /* Logs Dashboard */
        .dashboard {
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            width: 95%;
            max-width: 1400px;
            height: 88vh;
            border-radius: 12px;
            padding: 25px;
            overflow-y: auto;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .dashboard-title {
            font-size: 1.6em;
            color: #ffffff;
            font-weight: 600;
        }

        .tabs {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .tab {
            padding: 8px 16px;
            border: 1px solid #2a2a40;
            background: transparent;
            color: #9b9baa;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
            font-size: 0.88em;
        }

        .tab.active {
            background: #ff6b6b;
            color: white;
            border-color: #ff6b6b;
        }

        .tab:hover {
            border-color: #ff6b6b;
            color: #ff6b6b;
        }

        .data-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 18px;
        }

        .data-table thead {
            background: #0f0f23;
        }

        .data-table th {
            color: #c8c8d0;
            padding: 13px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #2a2a40;
        }

        .data-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #2a2a40;
            color: #e8e8e8;
            font-size: 0.9em;
        }

        .data-table tbody tr:hover {
            background: rgba(255, 107, 107, 0.05);
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }

        .badge.user-registration { background: #3b82f6; color: white; }
        .badge.user { background: #3b82f6; color: white; }
        .badge.character { background: #8b5cf6; color: white; }
        .badge.skill-purchase { background: #10b981; color: white; }
        .badge.skill_purchase { background: #10b981; color: white; }
        .badge.item-purchase { background: #f59e0b; color: white; }
        .badge.item_purchase { background: #f59e0b; color: white; }
        .badge.cheat-detected { background: #ef4444; color: white; }
        .badge.cheat_detected { background: #ef4444; color: white; }
        .badge.login-attempt { background: #06b6d4; color: white; }
        .badge.login_attempt { background: #06b6d4; color: white; }
        .badge.security-event { background: #ec4899; color: white; }
        .badge.security_event { background: #ec4899; color: white; }
        .badge.pvp-battle { background: #84cc16; color: white; }
        .badge.pvp_battle { background: #84cc16; color: white; }

        .loading-state {
            text-align: center;
            padding: 50px;
            font-size: 1.1em;
            color: #9b9baa;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #0f0f23;
        }

        ::-webkit-scrollbar-thumb {
            background: #2a2a40;
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #3a3a50;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .gateway-card {
                padding: 35px 25px;
            }

            h1 {
                font-size: 1.6em;
            }

            .question {
                font-size: 1em;
            }

            .footer-info {
                position: static;
                margin-bottom: 15px;
                max-width: 100%;
            }

            .header-controls {
                position: static;
                margin-top: 15px;
                justify-content: center;
                flex-wrap: wrap;
            }

            .logs-button {
                width: 100%;
            }

            .modal-box {
                width: 95%;
                padding: 28px 22px;
            }

            .dashboard {
                width: 100%;
                height: 100vh;
                border-radius: 0;
                padding: 18px;
            }

            .dashboard-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .data-table {
                font-size: 0.82em;
            }

            .data-table th,
            .data-table td {
                padding: 10px 8px;
            }
        }
    </style>
</head>
<body>
    <div class="footer-info">
        All rights reserved by Ninja Sage. Play Ninja Sage only at 
        <a href="https://ninjasage.id" target="_blank">https://ninjasage.id</a>
    </div>

    <div class="header-controls">
        <div class="status-indicator">
            <div class="status-dot connected" id="statusDot"></div>
            <span class="status-text connected" id="statusText">Connected</span>
        </div>
        <button class="logs-button" onclick="showLogin()">📊 LOGS</button>
    </div>

    <div class="container">
        <div class="gateway-card">
            <div class="ninja-icon">🥷</div>
            <h1>Welcome to Mhantappu Saga Gateway</h1>
            <p class="question">What are you doing here?</p>
            <span class="server-name">Mhantappu Saga Private Server</span>
        </div>
    </div>

    <!-- Login Overlay -->
    <div id="loginOverlay" class="overlay">
        <div class="modal-box">
            <button class="close-btn" onclick="hideLogin()">×</button>
            <h2>Admin Login</h2>
            <span class="warning-badge">⚠️ Admin Only!</span>
            <div class="form-field">
                <label>Username</label>
                <input type="text" id="username" placeholder="Enter username">
            </div>
            <div class="form-field">
                <label>Password</label>
                <input type="password" id="password" placeholder="Enter password">
            </div>
            <button class="submit-btn" onclick="doLogin()">LOGIN</button>
            <div id="errorMsg" class="error-msg"></div>
        </div>
    </div>

    <!-- Logs Dashboard Overlay -->
    <div id="dashboardOverlay" class="overlay">
        <div class="dashboard">
            <button class="close-btn" onclick="hideDashboard()">×</button>
            <div class="dashboard-header">
                <h2 class="dashboard-title">📊 System Logs Monitor</h2>
               <div class="tabs">
    <button class="tab active" onclick="switchTab('registered')">Registered</button>
    <button class="tab" onclick="switchTab('users')">Users</button>
    <button class="tab" onclick="switchTab('characters')">Characters</button>
    <button class="tab" onclick="switchTab('skills')">Skills</button>
    <button class="tab" onclick="switchTab('items')">Items</button>
    <button class="tab" onclick="switchTab('login_logs')">Logins</button>
    <button class="tab" onclick="switchTab('cheat_logs')">Cheats</button>
    <button class="tab" onclick="switchTab('security_events')">Security</button>
    <button class="tab" onclick="switchTab('pvp_battles')">PVP</button>
</div>
            </div>
            <div id="tableContent">
                <div class="loading-state">Loading logs...</div>
            </div>
        </div>
    </div>

    <script>
        let token = null;
        let activeTab = 'registered';
        let gatewayStatus = 'connected';
        let statusCheckInterval = null;

        // Gateway Status Check
        function updateGatewayStatus(status) {
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');
            
            dot.className = `status-dot ${status}`;
            text.className = `status-text ${status}`;
            
            switch(status) {
                case 'connected':
                    text.textContent = 'Connected';
                    break;
                case 'disconnected':
                    text.textContent = 'Disconnected';
                    break;
                case 'reconnecting':
                    text.textContent = 'Reconnecting...';
                    break;
            }
            
            gatewayStatus = status;
        }

        async function checkGatewayStatus() {
            try {
                const response = await fetch('{{ url("/amf/status") }}', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'active') {
                        updateGatewayStatus('connected');
                    } else {
                        updateGatewayStatus('disconnected');
                    }
                } else {
                    updateGatewayStatus('disconnected');
                }
            } catch (error) {
                updateGatewayStatus('reconnecting');
            }
        }

        // Auto check every 10 seconds
        function startStatusMonitoring() {
            checkGatewayStatus();
            statusCheckInterval = setInterval(checkGatewayStatus, 10000);
        }

        function stopStatusMonitoring() {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
            }
        }

        function showLogin() {
            document.getElementById('loginOverlay').classList.add('show');
        }

        function hideLogin() {
            document.getElementById('loginOverlay').classList.remove('show');
            document.getElementById('errorMsg').textContent = '';
        }

        function hideDashboard() {
            document.getElementById('dashboardOverlay').classList.remove('show');
        }

        async function doLogin() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const error = document.getElementById('errorMsg');

            if (!username || !password) {
                error.textContent = 'Please enter both username and password';
                return;
            }

            try {
                const res = await fetch('{{ url("/amf/admin-login") }}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();

                if (data.success) {
                    token = data.token;
                    hideLogin();
                    showDashboard();
                } else {
                    error.textContent = data.message || 'Login failed';
                }
            } catch (e) {
                error.textContent = 'Connection error. Please try again.';
            }
        }

        function showDashboard() {
        document.getElementById('dashboardOverlay').classList.add('show');
        fetchLogs('registered');
    }

        async function fetchLogs(type) {
            activeTab = type;
            const content = document.getElementById('tableContent');
            content.innerHTML = '<div class="loading-state">Loading logs...</div>';

            try {
                const res = await fetch(`{{ url("/amf/get-logs") }}?type=${type}`, {
                    headers: {
                        'X-Admin-Token': token
                    }
                });

                if (res.status === 401) {
                    hideDashboard();
                    showLogin();
                    document.getElementById('errorMsg').textContent = 'Session expired. Please login again.';
                    return;
                }

                const data = await res.json();

                if (data.success) {
                    renderTable(data.logs);
                } else {
                    content.innerHTML = '<div class="loading-state">Failed to load logs</div>';
                }
            } catch (e) {
                content.innerHTML = '<div class="loading-state">Error loading logs</div>';
            }
        }

        function renderTable(logs) {
    const content = document.getElementById('tableContent');
    
    if (!logs || logs.length === 0) {
        content.innerHTML = '<div class="loading-state">No logs found</div>';
        return;
    }

    let html = '<table class="data-table"><thead><tr>';
    html += '<th>Type</th><th>Details</th><th>Timestamp</th>';
    html += '</tr></thead><tbody>';

    logs.forEach(log => {
        const type = log.type || 'unknown';
        let info = '';

        switch(type) {
            case 'user_registration':
                // Langsung ambil dari field 'detail'
                info = log.detail || `${log.username} bergabung ke Mhantappu Saga!`;
                break;
            case 'user':
                info = `User: ${log.username} | Email: ${log.email} | Type: ${log.account_type} | Tokens: ${log.tokens}`;
                break;
            case 'character':
                info = `Character: ${log.name} | Owner: ${log.owner} | Lv.${log.level} | Gold: ${log.gold} | TP: ${log.tp}`;
                break;
            case 'skill_purchase':
                info = `${log.character} (${log.owner}) purchased skill: ${log.skill_id}`;
                break;
            case 'item_purchase':
                info = `${log.character} (${log.owner}) bought ${log.quantity}x ${log.item_id}`;
                break;
            case 'cheat_detected':
                info = `🚨 ${log.username} | ${log.reason} | IP: ${log.ip_address} | Target: ${log.target}`;
                break;
            case 'login_attempt':
                info = `User: ${log.username} | Success: ${log.success} | IP: ${log.ip_address} | Reason: ${log.reason || 'N/A'}`;
                break;
            case 'security_event':
                info = `Event: ${log.event_type} | IP: ${log.ip_address}`;
                break;
            case 'pvp_battle':
                info = `${log.host} vs ${log.enemy} | Winner: ${log.winner} | Trophy Δ: ${log.trophy_delta}`;
                break;
            default:
                info = log.detail || JSON.stringify(log);
        }

        const badgeClass = type.replace('_', '-');
        html += `<tr>
            <td><span class="badge ${badgeClass}">${type.replace('_', ' ')}</span></td>
            <td>${info}</td>
            <td>${log.timestamp || log.created_at || 'N/A'}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    content.innerHTML = html;
}

        function switchTab(type) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            fetchLogs(type);
        }

        // Initialize status monitoring when page loads
        window.addEventListener('load', () => {
            startStatusMonitoring();
        });

        // Clean up interval when page unloads
        window.addEventListener('beforeunload', () => {
            stopStatusMonitoring();
        });
    </script>
</body>
</html>