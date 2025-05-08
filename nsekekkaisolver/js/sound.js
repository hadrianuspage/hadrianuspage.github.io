
    // Function to play the click sound
    function playClickSound() {
        const clickSound = document.getElementById('click-sound');
        clickSound.currentTime = 0; // Reset to start
        clickSound.play().catch(error => {
            console.error("Playback failed:", error);
        });
    }
    
    // Select all buttons and add the click event listener
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', playClickSound);
    });




    // Show volume settings modal
document.getElementById('volumeSettingsButton').onclick = function() {
    document.getElementById('volumeSettingsModal').style.display = 'flex';
};

// Volume control functionality
const audioElement = document.getElementById('background-music');
const volumeLabel = document.getElementById('volumeLabel');

document.getElementById('volumeUp').onclick = function() {
    if (audioElement.volume < 1) {
        audioElement.volume += 0.1;
        updateVolumeLabel();
    }
};

document.getElementById('volumeDown').onclick = function() {
    if (audioElement.volume > 0) {
        audioElement.volume -= 0.1;
        updateVolumeLabel();
    }
};

function updateVolumeLabel() {
    volumeLabel.textContent = `Volume: ${(audioElement.volume * 100).toFixed(0)}%`;
}

// Save volume functionality
document.getElementById('saveVolumeButton').onclick = function() {
    localStorage.setItem('volume', audioElement.volume);
    alert('Volume saved!');
};

// Load saved volume on page load
window.onload = function() {
    const savedVolume = localStorage.getItem('volume');
    if (savedVolume) {
        audioElement.volume = parseFloat(savedVolume);
        updateVolumeLabel();
    }
};

// Ensure the volume label reflects the initial volume
updateVolumeLabel();
