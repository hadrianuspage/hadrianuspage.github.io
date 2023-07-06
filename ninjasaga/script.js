function useJutsu(jutsu) {
  switch (jutsu) {
    case 'Rasengan':
      // Logika untuk menggunakan jutsu Rasengan
      console.log('Menggunakan jutsu Rasengan');
      break;
    case 'Chidori':
      // Logika untuk menggunakan jutsu Chidori
      console.log('Menggunakan jutsu Chidori');
      break;
    case 'KageBunshin':
      // Logika untuk menggunakan jutsu Kage Bunshin
      console.log('Menggunakan jutsu Kage Bunshin');
      break;
    default:
      console.log('Jutsu tidak ditemukan');
  }
}
