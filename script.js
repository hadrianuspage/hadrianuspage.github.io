function changeLink() {
    var link = document.getElementById("mylink");

    window.open( 
      link.href, 
      '_blank' 
    ); 

    link.innerHTML = "facebook"; 
    link.setAttribute('href', "http://facebook.com"); 

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
