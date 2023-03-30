function changeLink() {
    var link = document.getElementById("mylink");

    window.open( 
      link.href, 
      '_blank' 
    ); 

    link.innerHTML = "mediafire"; 
    link.setAttribute('href', "https://www.mediafire.com/file/jwcnsl9m1mtk03u/Minecraft_base.apk/file"); 

    return false; 
}


var tombolMenu = document.getElementsByClassName('tombol-menu')[0];
var menu = document.getElementsByClassName('menu')[0];

tombolMenu.onclick = function() {
    menu.classList.toggle('active');
}

menu.onclick = function() {
    menu.classList.toggle('active');
}
