
    // Function to update the timer
    function updateTimer() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        document.getElementById('timer').textContent = `${hours}:${minutes}:${seconds}`;
    }
    
    // Update the timer every second
    setInterval(updateTimer, 1000);
    // Initialize the timer immediately
    updateTimer();
