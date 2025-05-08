    // Open encyclopedia modal
    document.getElementById("visitEncyclopediaButton").onclick = function() {
        window.open('https://hadrianuspage.my.id/nsekekkaisolver/services/ninjasage/encyclopedia/index.html');
    };
    
    // Open iframe modal
    document.getElementById("openFrameButton").onclick = function() {
        document.getElementById('iframeModal').style.display = 'flex';
    };
    document.getElementById("closeEncyclopediaButton").onclick = function() {
    document.getElementById('encyclopediaPopup').style.display = 'none'; // Close the modal
};
document.getElementById("closeEncyclopediaFrame").onclick = function() {
    document.getElementById('iframeModal').style.display = 'none'; // Close the modal
};