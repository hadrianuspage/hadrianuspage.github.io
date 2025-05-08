// Support Me Modal functionality
document.getElementById("supportMeButton").onclick = function() {
    document.getElementById("supportMeModal").style.display = "flex";
};

document.getElementById("noSupportButton").onclick = function() {
    document.getElementById("supportMeModal").style.display = "none";
};

document.getElementById("yesSupportButton").onclick = function() {
    window.open('https://saweria.co/hadrianus', '_blank');
};

window.onclick = function(event) {
    if (event.target == document.getElementById("supportMeModal")) {
        document.getElementById("supportMeModal").style.display = "none";
    }
};

// Chat modal functionality
function openChat() {
    document.getElementById("chatModal").style.display = "flex";
}

function closeChat() {
    document.getElementById("chatModal").style.display = "none";
}

Handlebars.registerHelper('range', function(min, max) {
    const result = [];
    for (let i = min; i <= max; i++) {
        result.push(i);
    }
    return result;
});

window.onload = function() {
    setTimeout(function() {
        document.getElementById('loading').style.display = 'none';
        document.querySelector('.hidden-content').style.display = 'block';
        // Set initial background with lazy loading
        const initialBg = document.body.style.backgroundImage = "url('https://hadrianuspage.my.id/nsekekkaisolver/images/mentahan_ns_aniv_full.jpg')";
        document.body.style.backgroundSize = "cover";
        document.body.style.backgroundPosition = "center";

        // Array of image URLs
        const images = [
            "https://hadrianuspage.my.id/nsekekkaisolver/images/sage_heroes.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/3rd_anniversary_ninja_sage.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/indoneisan_ninja.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/red_fight.jpeg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/summer_night_2023.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/bg-summer.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/annivbg1.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/annivbg2.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/annivbg3.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/annivbg4.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/NNSG.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/IMG_6930.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/1_NSE_3rd_Anniv.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/1000229047.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/anniversary.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/final2.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/IMG_8302.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Picsart_25-03-09_19-56-20-682.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Happy_Bday_NSage_by_Labbaik_Chicken.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/3rd_Anniv_Ninjasage.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Picsart_25-03-06_03-19-18-709.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/FanArt.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/1000228256.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/ReinikaIFFFanartNS3rdAn.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/test123.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/500Token.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/IMG-20250228-WA0000.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Aniv_3rd_NSE.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/export202502270758182880.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Ninjasage.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/NINJASAGE.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/ninjasage_new_last_copy.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Hehe_Aniv_NSE_3rd.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/encisjokifanart_anniv3rd_nse.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Picsart_25-02-26_13-21-57-267.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/FE31FA21-9C28-4F16-8CC7-520C4E2EBA94.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Ninja_Sage_3rd_Annivesary_Zerna.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/fansart_ninjasage_1.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/anniversary_ninja_sage_3RD.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/BackgroundEraser_20250226_020910757.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Picsart_25-02-25_11-09-41-812.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/ninjasage_3rd_event.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/IMG_3965.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/Halloween.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/IMG_3137.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/garuda_event_2023.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/kappa.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/christmas_x_new_year_by_dandi.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/ninja_sage_chinese_new_years.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/3_fan_art_ramadhan_2023_qIFDk.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/salus_event.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/fox_pack.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/christmas_x_new_year_by_seres.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/christmas_x_new_year_by_kaza.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/easter_holiday.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/valentine_2023.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/halloween_by_serestia_aCJfL.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/halloween_by_reiji_id_xwcCx.jpg",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/2nd-anniv-1.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/sunrakushoot.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/sunrakustrike.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/image-40.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/1746032545-picsay.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/1746032577-picsay.png",
            "https://hadrianuspage.my.id/nsekekkaisolver/images/fox_deity.png"
        ];

        // Function to change background image with lazy loading
        function changeBackgroundImage() {
            const randomIndex = Math.floor(Math.random() * images.length);
            const imageUrl = images[randomIndex];

            // Create a new image element
            const img = new Image();
            img.src = imageUrl;

            // Set the background image once the image is loaded
            img.onload = () => {
                document.body.style.backgroundImage = `url('${imageUrl}')`;
            };
        }

        // Change image every 25 seconds
        setInterval(changeBackgroundImage, 25000);
    }, 2800);
};

// Array of music file URLs
const musicFiles = [
    "musics/Ninja Saga - An Adventure Awaits.mp3",
    "musics/Aimer - Zero.mp3",
    "musics/Ninja Saga - Okaeri.mp3",
    "musics/Dj Drop Only.mp3",
    "musics/DJ Under.mp3",
    "musics/y2mate.com - Dxrk ダーク  RAVE.mp3",
    "musics/y2mate.com - All Around The World La La La.mp3",
    "musics/y2mate.com - Robin Hustin x TobiMorrow  Light It Up feat Jex NCS Release.mp3",
    "musics/y2mate.com - 真夜中のドア Stay With Me  松原みき Miki Matsubara  Cover by Chris Andrian Yang.mp3",
    "musics/y2mate.com - 5th Anniversary Menu Theme  Guy  Hatake Drum Stars  Naruto x Boruto Ninja Voltage.mp3",
    "musics/y2mate.com - Lost Saga BGM  Wild West.mp3",
    "musics/Breaking Benjamin - Failure.mp3",
    "musics/y2mate.com - alan walker  ava max  alone pt ii slowed  reverb.mp3",
    "musics/y2mate.com - Alley Cat.mp3",
    "musics/y2mate.com - Ascence  Konnichiwa NCS Release.mp3",
    "musics/y2mate.com - Convex  4U feat Jex Jordyn NCS Release.mp3",
    "musics/y2mate.com - DJ UNITY TIK TOK VIRAL TERBARU 2021.mp3",
    "musics/y2mate.com - Egzod  Rise Up ft Veronica Bravo  MIME NCS Release.mp3",
    "musics/y2mate.com - FateStay Night OP2  Brave ShineCover by Raon Lee.mp3",
    "musics/y2mate.com - Fukashigi no Carte Type Beat Prod Heaven.mp3",
    "musics/y2mate.com - Guilty Crown  My Dearest Opening  ENGLISH Ver  AmaLee.mp3",
    "musics/y2mate.com - In The End Official Lyric Video  Linkin Park.mp3",
    "musics/y2mate.com - in the stars benson boone sped up.mp3",
    "musics/y2mate.com - indila  love story tiktok remix.mp3",
    "musics/y2mate.com - Joji  Glimpse of Us Lyrics.mp3",
    "musics/y2mate.com - Julius Dreisig  Zeus X Crona  Invisible NCS Release.mp3",
    "musics/y2mate.com - MysticSwe  mystical By iKorbon descripción.mp3"

];

// Function to populate the dropdown with music files
function populateMusicDropdown() {
    const musicDropdown = document.getElementById('musicDropdown');

    // Clear existing options
    musicDropdown.innerHTML = '';

    musicFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file;
        option.textContent = file.split('/').pop(); // Display the file name
        musicDropdown.appendChild(option);
    });
}

// Open music modal
document.getElementById("changeMusicButton").onclick = function() {
    document.getElementById('musicModal').style.display = 'flex';
    populateMusicDropdown(); // Populate dropdown when modal opens
};

// Handle music change
document.getElementById("changeMusic").onclick = function() {
    const selectedMusic = document.getElementById('musicDropdown').value;
    const fileInput = document.getElementById('fileInput');
    const audioElement = document.getElementById('background-music');

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileURL = URL.createObjectURL(file);
        audioElement.src = fileURL; // Set the source to the selected file
    } else {
        audioElement.src = selectedMusic; // Fall back to dropdown selection
    }

    audioElement.play(); // Play the new music
    alert(`Now playing: ${fileInput.files.length > 0 ? file.name : selectedMusic.split('/').pop()}`);

    // Close the music modal
    document.getElementById('musicModal').style.display = 'none';
};

// Close modal when clicking outside of it
function closeMusicModal() {
    document.getElementById('musicModal').style.display = 'none';
}

// Close modal when clicking outside of it
document.getElementById('musicModal').onclick = function(event) {
    if (event.target === this) {
        closeMusicModal(); // Call the close function
    }
};

// Attach close functionality to the close button
document.querySelectorAll('.close').forEach(function(closeButton) {
    closeButton.onclick = function() {
        const modal = this.closest('.modal'); // Find the closest modal
        modal.style.display = 'none'; // Hide the modal
    };
});

document.getElementById('start').onclick = function() {
    this.disabled = true; // Disable the button
    const randomIndex = Math.floor(Math.random() * musicFiles.length);
    const selectedMusic = musicFiles[randomIndex];

    const audioElement = document.getElementById('background-music');
    audioElement.src = selectedMusic; // Set the source to the random song
    audioElement.play().then(() => {

        document.getElementById('stop-button-container').style.display = 'block'; // Show Stop button
    }).catch(error => {
        console.error("Playback failed:", error); // Handle playback errors
    }).finally(() => {
        this.disabled = false; // Re-enable the button after handling
    });
};

document.getElementById('stop').onclick = function() {
    const audioElement = document.getElementById('background-music');
    audioElement.pause();
    audioElement.currentTime = 0; // Reset to start
    document.getElementById('stop-button-container').style.display = 'none'; // Hide Stop button
};

document.getElementById('pause').onclick = function() {
    audioElement.pause();
    this.style.display = 'none'; // Hide Pause button
    document.getElementById('resume').style.display = 'inline-block'; // Show Resume button
};

document.getElementById('resume').onclick = function() {
    audioElement.play();
    this.style.display = 'none'; // Hide Resume button
    document.getElementById('pause').style.display = 'inline-block'; // Show Pause button
};
document.getElementById('pause').onclick = function() {
    audioElement.pause();
    this.style.display = 'none'; // Hide Pause button
    document.getElementById('resume').style.display = 'inline-block'; // Show Resume button
};

document.getElementById('resume').onclick = function() {
    audioElement.play();
    this.style.display = 'none'; // Hide Resume button
    document.getElementById('pause').style.display = 'inline-block'; // Show Pause button
};

var modal = document.getElementById("popupModal");
var btn = document.getElementById("openPopup");
var span = document.getElementsByClassName("close")[0];

btn.onclick = function() {
    modal.style.display = "flex";
};

span.onclick = function() {
    modal.style.display = "none";
};

document.getElementById("visitSageSealBox").onclick = function() {
    document.getElementById('sageSealModal').style.display = 'flex';
};

// Close modal when clicking outside of it
window.onclick = function(event) {
    if (event.target == sageSealModal) {
        sageSealModal.style.display = "none";
    }
};

var discordModal = document.getElementById("discordModal");
var logo = document.getElementById("logo");

logo.onclick = function() {
    discordModal.style.display = "flex";
};

document.getElementById("noButton").onclick = function() {
    discordModal.style.display = "none";
};

document.getElementById("yesButton").onclick = function() {
    window.open('https://discord.gg/ninjasage', '_blank');
};

window.onclick = function(event) {
    if (event.target == discordModal) {
        discordModal.style.display = "none";
    }
    if (event.target == chatModal) {
        closeChat();
    }
    if (event.target == modal) {
        modal.style.display = "none";
    }
};