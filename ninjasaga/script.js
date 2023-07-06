// Dummy data for player
const playerData = {
  username: "",
  hp: 100,
  cp: 50,
  exp: 0,
  tokens: 0,
  gold: 0,
};

// Function to handle login
function login() {
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  
  // Validate login credentials
  // Example validation, replace with your own logic
  if (usernameInput.value === "username" && passwordInput.value === "password") {
    playerData.username = usernameInput.value;

    // Update UI with player stats
    document.getElementById("player-username").textContent = playerData.username;
    document.getElementById("player-hp").textContent = playerData.hp;
    document.getElementById("player-cp").textContent = playerData.cp;
    document.getElementById("player-exp").textContent = playerData.exp;
    document.getElementById("player-tokens").textContent = playerData.tokens;
    document.getElementById("player-gold").textContent = playerData.gold;

    // Show game container, hide login container
    document.getElementById("login-container").style.display = "none";
    document.getElementById("game-container").style.display = "block";
  } else {
    alert("Invalid username or password");
  }
}

// Function to startmission
function startMission() {
  // Perform mission logic here

  // Update player stats

  // Update UI with player stats
}

// Function to go to the Academy
function goToAcademy() {
  // Perform academy logic here

  // Update player stats

  // Update UI with player stats
}

// Function to go to the Hunting House
function goToHuntingHouse() {
  // Perform Hunting House logic here

  // Update player stats

  // Update UI with player stats
}
