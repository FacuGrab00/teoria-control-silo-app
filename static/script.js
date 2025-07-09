const socket = io();

socket.on('nuevos_datos', data => {
  document.getElementById('temperatura').innerText = data.temperatura + " °C";
  document.getElementById('humedad').innerText = data.humedad + " %";
  document.getElementById('distancia').innerText = data.distancia + " cm";
});