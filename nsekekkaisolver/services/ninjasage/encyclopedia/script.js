
        let position = { x: 0, y: 0 };
        let audio = new Audio('https://hadrianuspage.my.id/nsekekkaisolver/musics/Okaeri2.mp3');
        let clickSound = new Audio('https://hadrianuspage.my.id/nsekekkaisolver/sounds/click/click.mp3');
        let volume = 1;

        function loadSWF() {
            window.RufflePlayer = window.RufflePlayer || {};
            const ruffle = window.RufflePlayer.newest();
            const player = ruffle.createPlayer();
            player.config = {
                showSwfDownload: false,
                splashscreen: false,
                autoplay: 'on',
                unmuteOverlay: 'hidden',
                allowScriptAccess: true,
                wmode: 'transparent',
                frameRate: 60
            };

            const container = document.getElementById("ruffle-player");
            container.innerHTML = '';
            container.appendChild(player);
            player.load({
                url: 'https://ns-assets.ninjasage.id/static/encyclopedia.swf',
                parameters: {
                    itemId: "wpn_01",
                    stopAnimation: false,
                    cdn: "https://ns-assets.ninjasage.id/static/releases/cdn/assets/"
                }
            });

            player.addEventListener('click', function() {
                clickSound.volume = volume;
                clickSound.play();
                audio.volume = volume;
                audio.play();
            });

            return player;
        }

        const player = loadSWF();

        function toggleMovementButtons() {
            const buttons = document.querySelectorAll('.movement-button');
            const shouldShow = buttons[0].style.display === 'none';

            buttons.forEach(button => {
                button.style.display = shouldShow ? 'block' : 'none';
            });
        }

        function showMusicPopup() {
            document.getElementById("overlay").style.display = 'block';
            document.getElementById("music-popup").style.display = 'block';
        }

        function showLinkPopup() {
            document.getElementById("overlay").style.display = 'block';
            document.getElementById("link-popup").style.display = 'block';
        }

        document.getElementById("left-button").addEventListener("click", function() {
            position.x -= 100;
            document.getElementById("ruffle-player").style.left = position.x + 'px';
        });

        document.getElementById("right-button").addEventListener("click", function() {
            position.x += 100;
            document.getElementById("ruffle-player").style.left = position.x + 'px';
        });

        document.getElementById("up-button").addEventListener("click", function() {
            position.y -= 100;
            document.getElementById("ruffle-player").style.top = position.y + 'px';
        });

        document.getElementById("down-button").addEventListener("click", function() {
            position.y += 100;
            document.getElementById("ruffle-player").style.top = position.y + 'px';
        });

        document.getElementById("close-popup").addEventListener("click", function() {
            document.getElementById("overlay").style.display = 'none';
            document.getElementById("music-popup").style.display = 'none';
        });

        document.getElementById("hide-label").addEventListener("click", function() {
            document.getElementById("ninja-label").style.display = 'none';
            document.getElementById("link-popup").style.display = 'none';
            document.getElementById("overlay").style.display = 'none';
        });

        document.getElementById("play-music").addEventListener("click", function() {
            audio.volume = volume;
            audio.play();
        });

        document.getElementById("stop-music").addEventListener("click", function() {
            audio.pause();
            audio.currentTime = 0;
        });

        document.getElementById("pause-music").addEventListener("click", function() {
            audio.pause();
        });

        document.getElementById("resume-music").addEventListener("click", function() {
            audio.play();
        });

        document.getElementById("volume-settings").addEventListener("click", function() {
            document.getElementById("volume-control").style.display = 'block';
        });

        document.getElementById("save-volume").addEventListener("click", function() {
            volume = document.getElementById("volume-slider").value / 250;
            audio.volume = volume;
            clickSound.volume = volume;
            alert("Volume set to " + (volume * 100).toFixed(0) + "%");
        });

        document.getElementById("join-discord").addEventListener("click", function() {
            window.open('https://discord.gg/ninjasage', '_blank');
        });

        document.getElementById("visit-website").addEventListener("click", function() {
            window.open('https://ninjasage.id', '_blank');
        });

        document.getElementById("close-link-popup").addEventListener("click", function() {
            document.getElementById("overlay").style.display = 'none';
            document.getElementById("link-popup").style.display = 'none';
        });

        // FPS Counter
        let lastFrameTime = performance.now();
        let frameCount = 0;

        function updateFPS() {
            frameCount++;
            const currentTime = performance.now();
            const deltaTime = currentTime - lastFrameTime;

            if (deltaTime >= 1000) {
                document.getElementById('fps-counter').innerText = `FPS: ${frameCount}`;
                frameCount = 0;
                lastFrameTime = currentTime;
            }

            requestAnimationFrame(updateFPS);
        }

        updateFPS(); // Start the FPS counter