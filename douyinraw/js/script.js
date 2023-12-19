let videoList = document.querySelectorAll('.video-list-container .list');
let currentIndex = 0;

videoList.forEach((vid, index) => {
    vid.onclick = () => {
        videoList.forEach(remove => { remove.classList.remove('active') });
        vid.classList.add('active');

        let src = vid.querySelector('.list-video').src;
        let title = vid.querySelector('.list-title').innerHTML;

        document.querySelector('.main-video-container .main-video').src = src;
        document.querySelector('.main-video-container .main-video').play();
        document.querySelector('.main-video-container .main-vid-title').innerHTML = title;

        currentIndex = index;
    };
});

let mainVideo = document.querySelector('.main-video-container .main-video');

document.querySelector('.main-video-container .skip-backward').onclick = () => {
    if (currentIndex > 0) {
        currentIndex--;
        playMainVideo();
    }
};

document.querySelector('.main-video-container .play-pause').onclick = () => {
    if (mainVideo.paused) {
        mainVideo.play();
    } else {
        mainVideo.pause();
    }
};

document.querySelector('.main-video-container .skip-forward').onclick = () => {
    if (currentIndex < videoList.length - 1) {
        currentIndex++;
        playMainVideo();
    }
};

function playMainVideo() {
    let selectedVideo = videoList[currentIndex];
    selectedVideo.classList.add('active');

    let src = selectedVideo.querySelector('.list-video').src;
    let title = selectedVideo.querySelector('.list-title').innerHTML;

    document.querySelector('.main-video-container .main-video').src = src;
    document.querySelector('.main-video-container .main-video').play();
    document.querySelector('.main-video-container .main-vid-title').innerHTML = title;
}
