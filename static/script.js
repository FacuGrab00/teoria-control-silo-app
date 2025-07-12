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

// Parámetros silo (se actualizan desde API)
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

// Función para agregar datos a gráficos con control de cantidad máxima (20)
function agregarDato(etiqueta, temp, hum, vol) {
  etiquetas.push(etiqueta);
  datosTemperatura.push(temp);
  datosHumedad.push(hum);
  datosVolumen.push(vol);

  if (etiquetas.length > 20) {
    etiquetas.shift();
    datosTemperatura.shift();
    datosHumedad.shift();
    datosVolumen.shift();
  }
}

// Cargar parámetros y datos históricos al iniciar
$(document).ready(async () => {
  try {
    // Cargar parámetros del silo
    const resParametros = await fetch('/parametros');
    const parametros = await resParametros.json();
    ALTURA_SILO = parametros.altura_silo;
    RADIO_SILO = parametros.radio_silo;

    // Cargar datos históricos
    const resDatos = await fetch('/datos_historicos');
    const datos = await resDatos.json();

    // Limpiar arrays antes de cargar (por si)
    etiquetas.length = 0;
    datosTemperatura.length = 0;
    datosHumedad.length = 0;
    datosVolumen.length = 0;

    // Asumimos que los arrays vienen sincronizados por índice y timestamp
    const len = Math.min(
      datos.temperatura?.length || 0,
      datos.humedad?.length || 0,
      datos.volumen?.length || 0
    );

    for (let i = 0; i < len; i++) {
      const hora = new Date(datos.temperatura[i].timestamp).toLocaleTimeString();
      const temp = Number(datos.temperatura[i].valor);
      const hum = Number(datos.humedad[i].valor);
      const vol = Number(datos.volumen[i].valor);

      agregarDato(hora, temp, hum, vol);
    }

    // Actualizar gráficos con datos iniciales
    chartTemp.update();
    chartHum.update();
    chartVol.update();

  } catch (e) {
    console.error('Error cargando datos iniciales:', e);
  }

  // Funcionalidad toggle estado ventilador (modo manual)
  const $btnApagado = $('.btn-estado-off');
  const $btnPrendido = $('.btn-estado-on');

  $('.btn-group-estado button').click(async function() {
    const nuevoEstado = $(this).data('estado'); // 'apagado' o 'encendido'
    let estadoValor = 2; // default apagado
    if (nuevoEstado === 'encendido') estadoValor = 1;

    // Bloquear botones mientras se procesa
    $('.btn-group-estado button').prop('disabled', true);

    try {
      const res = await fetch('/ventilador', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: estadoValor })
      });
      const json = await res.json();

      if (res.ok) {
        if (estadoValor === 1) {
          $btnPrendido.addClass('active');
          $btnApagado.removeClass('active');
        } else {
          $btnApagado.addClass('active');
          $btnPrendido.removeClass('active');
        }
        alert(json.mensaje);
      } else {
        alert(json.error || "Error al cambiar estado del ventilador");
      }
    } catch (e) {
      alert("Error de comunicación con el servidor");
      console.error(e);
    } finally {
      $('.btn-group-estado button').prop('disabled', false);
    }
  });
});

// Actualizar datos al recibirlos por socket en tiempo real
socket.on('nuevos_datos', data => {
  const now = new Date().toLocaleTimeString();

  // Calcular volumen usando parámetros actuales
  const distEnMetros = Number(data.distancia) / 100;
  const alturaMaterial = ALTURA_SILO - distEnMetros;
  const volumen = Math.PI * Math.pow(RADIO_SILO, 2) * alturaMaterial;

  agregarDato(
    now,
    Number(data.temperatura),
    Number(data.humedad),
    volumen.toFixed(2)
  );

  // Actualizar textos en HTML
  $tempDiv.text(data.temperatura + " °C");
  $humDiv.text(data.humedad + " %");
  $distDiv.text(data.distancia + " cm");
  $volumenDiv.text(volumen.toFixed(2) + " m³");

  // Actualizar gráficos
  chartTemp.update();
  chartHum.update();
  chartVol.update();
});
