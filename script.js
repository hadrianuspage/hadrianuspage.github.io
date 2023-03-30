let buttonLink = document.getElementById("link");
let link = buttonLink.getAttributeNode("href").value;
console.log(link)


buttonLink.addEventListener("click", function(){
  buttonLink.addEventListener("click", function(){
  buttonLink.setAttribute("href", "url-asli-disini")
  buttonLink.removeAttribute("target")
})
})

var tombolMenu = document.getElementsByClassName('tombol-menu')[0];
var menu = document.getElementsByClassName('menu')[0];

tombolMenu.onclick = function() {
    menu.classList.toggle('active');
}

menu.onclick = function() {
    menu.classList.toggle('active');
}
