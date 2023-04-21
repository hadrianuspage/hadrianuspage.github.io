const pattern = /^[^&%<>,.^]*[a-zA-Z\s]+[^&%<>,.^]*$/;


let user = '';

do {
  user = window.prompt('Masuk Quiz ketik (y) :');
} while (!pattern.test(user));


const containerSatu = document.querySelector(".questions");
function getSoal(){
  return new Promise(function(resolve, reject){

  var getQuestion = new XMLHttpRequest();
  getQuestion.open("GET", "res/question.json", true);
  
  getQuestion.onloadend = function(){
    var questions = JSON.parse(this.responseText)
    resolve(questions)
  }
  
  getQuestion.send()

  })
}

getSoal()
.then(function(questions){
 let questionContainer = questions;
 questionContainer.sort(() => Math.random() - 0.5);
 let randomedQuestion = [];
 for(g = 0; g < 10; g++){
 randomedQuestion.push(questionContainer[g])
 }
 
 
for (let i = 0; i < 10; i++) {
  const randomedQuestion = document.createElement("div");
  randomedQuestion.classList.add("qStyle");

  const questionText = questions[i].question;
  const questionHTML = `<h2>${questionText}</h2>`;
  randomedQuestion.innerHTML = questionHTML;

  for (x = 0; x < 5; x++) {
    const newChoice = document.createElement("div");
    const newChoiceText = document.createTextNode(`${questions[i].options[x]}`);
    newChoice.classList.add(x)
    newChoice.classList.add("pilihan");
    
  newChoice.appendChild(newChoiceText)
  randomedQuestion.appendChild(newChoice)
  
  }
  randomedQuestion.classList.add("containers")
  containerSatu.appendChild(randomedQuestion);
}


const containers = document.querySelectorAll(".containers");

containers.forEach((container) => {
  const boxes = container.querySelectorAll(".pilihan");
  let divAktif;

  boxes.forEach((box) => {
    box.addEventListener("click", function() {
      if (divAktif) {
        divAktif.classList.remove("terpilih");
      }
      box.classList.add("terpilih");
      divAktif = box;
    });
  });
});

const doneBtn = document.querySelector(".done");
doneBtn.addEventListener("click", function(){
  const getJawaban = document.querySelectorAll(".terpilih");
  let containerJawaban = [];
  let jawabanDB = [];
  let score = 0;
  
  for(h = 0; h < 10; h++){
    jawabanDB.push(questions[h].answer);
  }
  
  getJawaban.forEach((jawabanUser) => {
    
    containerJawaban.push(jawabanUser.innerText)
    
  })
  
  const scoreContainer = document.getElementById("scoreContainer");
  const scoreBody = document.querySelector("#scoreContainer .scoreBody")

  
  
  for (let o = 0; o < containerJawaban.length; o++) {
  if (jawabanDB.includes(containerJawaban[o])) {
    score++;
  }
}
  
  scoreContainer.style.display = "block";
  scoreBody.innerHTML = `Selamat ${user}, kamu benar ${score}` + "<br>Terima kasih telah berpartisipasi! >_< <br>Halaman ini akan dimuat ulang dalam 5 detik";
  
  setTimeout(function() {
    window.location.href = window.location.href;
  }, 5000);
  
  
  console.log(jawabanDB)
  console.log(containerJawaban)
})


 
})
