const socket = io('http://localhost:5000');

const $tempDiv = $('#temperatura');
const $humDiv = $('#humedad');
const $distDiv = $('#distancia');
const $volumenDiv = $('#volumen');

// Arrays para gráficas
const datosTemperatura = [];
const datosHumedad = [];
const datosDistancia = [];
const datosVolumen = [];
const etiquetas = [];

// Parámetros silo
let ALTURA_SILO = 1.0;
let RADIO_SILO = 0.05;

// Gráficos Chart.js
const ctxTemp = $('#graficoTemp')[0].getContext('2d');
const chartTemp = new Chart(ctxTemp, {
  type: 'line',
  data: {
    labels: etiquetas,
    datasets: [{
      label: 'Temperatura (°C)',
      data: datosTemperatura,
      borderColor: 'rgba(255,99,132,1)',
      backgroundColor: 'rgba(255,99,132,0.2)',
      fill: true,
      tension: 0.3,
      pointRadius: 5
    }]
  },
  options: {
    scales: {
      x: { title: { display: true, text: 'Hora' }},
      y: { beginAtZero: false }
    }
  }
});

const ctxHum = $('#graficoHum')[0].getContext('2d');
const chartHum = new Chart(ctxHum, {
  type: 'line',
  data: {
    labels: etiquetas,
    datasets: [{
      label: 'Humedad (%)',
      data: datosHumedad,
      borderColor: 'rgba(54,162,235,1)',
      backgroundColor: 'rgba(54,162,235,0.2)',
      fill: true,
      tension: 0.3,
      pointRadius: 5
    }]
  },
  options: {
    scales: {
      x: { title: { display: true, text: 'Hora' }},
      y: { beginAtZero: true }
    }
  }
});

const ctxVol = $('#graficoVol')[0].getContext('2d');
const chartVol = new Chart(ctxVol, {
  type: 'line',
  data: {
    labels: etiquetas,
    datasets: [{
      label: 'Volumen (m³)',
      data: datosVolumen,
      borderColor: 'rgba(255,206,86,1)',
      backgroundColor: 'rgba(255,206,86,0.2)',
      fill: true,
      tension: 0.3,
      pointRadius: 5
    }]
  },
  options: {
    scales: {
      x: { title: { display: true, text: 'Hora' }},
      y: { beginAtZero: true }
    }
  }
});

// Actualizar datos al recibirlos por socket
socket.on('nuevos_datos', data => {
  const now = new Date().toLocaleTimeString();

  etiquetas.push(now);
  datosTemperatura.push(Number(data.temperatura));
  datosHumedad.push(Number(data.humedad));
  datosDistancia.push(Number(data.distancia));

  const distEnMetros = Number(data.distancia) / 100;
  const alturaMaterial = ALTURA_SILO - distEnMetros;
  const volumen = Math.PI * Math.pow(RADIO_SILO, 2) * alturaMaterial;
  datosVolumen.push(volumen.toFixed(2));

  if (etiquetas.length > 20) {
    etiquetas.shift();
    datosTemperatura.shift();
    datosHumedad.shift();
    datosDistancia.shift();
    datosVolumen.shift();
  }

  $tempDiv.text(data.temperatura + " °C");
  $humDiv.text(data.humedad + " %");
  $distDiv.text(data.distancia + " cm");
  $volumenDiv.text(volumen.toFixed(2) + " m³");

  chartTemp.update();
  chartHum.update();
  chartVol.update();
});

// Ejecutar al cargar la página
$(document).ready(async () => {
  try {
    const resParametros = await fetch('/parametros');
    const parametros = await resParametros.json();

    ALTURA_SILO = parametros.altura_silo;
    RADIO_SILO = parametros.radio_silo;
  } catch (e) {
    console.error('Error cargando parámetros iniciales:', e);
  }
});
