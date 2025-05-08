
    // Instructions button functionality
    document.getElementById("instructionsButton").onclick = function() {
        document.getElementById("instructionsModal").style.display = "flex";
    };
    
// English instructions
document.getElementById("engButton").onclick = function() {
    document.getElementById("instructionText").innerHTML = `
        <p><strong>Kekkai Solver Instructions:</strong></p>
        <pre>
1. <strong>Stage 3 Jounin Exam Stage:</strong>
   There are 4 patterns (2, 3, 4, 5)

2. <strong>Website:</strong>
   Go to the nsekekaiasolver website
   Ignore "available runes"
   Select "number of runes required"

3. <strong>Stage 3 Jounin Exam Pattern 2:</strong>
   Select dropdown 2, click "start"
   Note the "green position" (left)
   "yellow position" (right)
   On the game
   Enter according to the game pattern
   (e.g., "green, white") to the website
   For right place is green
   For wrong place is yellow
   Adjust the pattern (e.g "1 0" or "0 1")
   on the website
   not must "1 0" or "0 1"
   just follow pattern on the game
   and input into website

4. <strong>Patterns 3, 4, and 5:</strong>
   Follow the same steps 
   as pattern 2 above
   
5. <strong>For Sage Seal :</strong>
    follow the instructions above
    the numbers are 2,3,4,5 and 6
        </pre>
    `;
};

// Indonesian instructions
document.getElementById("indButton").onclick = function() {
    document.getElementById("instructionText").innerHTML = `
        <p><strong>Kekkai Solver Instructions:</strong></p>
        <pre>
1. <strong>Stage 3 Jounin Exam Stage:</strong>
   Ada 4 pola (2, 3, 4, 5)

2. <strong>Website:</strong>
   Masuk ke website nsekekaiasolver
   Abaikan "available runes"
   Pilih "number of runes required"

3. <strong>Stage 3 Jounin Exam Pola 2:</strong>
   Pilih dropdown 2, klik "start"
   Catat "green position" (kiri) 
   "yellow position" (kanan)
   Di Game
   Masukkan sesuai pola dari game
   (misal "green, white") ke website
   Untuk Right Place itu green
   Untuk Wrong Place itu yellow
   Sesuaikan pola (misal "1 0" atau "0 1")
   di website
   tidak harus "1 0" atau "0 1"
   ikuti pola di game
   dan masukan ke website

4. <strong>Pola 3, 4, dan 5:</strong>
   Ikuti langkah yang sama
   dengan pola 2 di atas
   
5. <strong>For Sage Seal :</strong>
ikuti semua petunjuk di atas
angkanya adalah 2,3,4,5 dan 6
</pre>
    `;
};

