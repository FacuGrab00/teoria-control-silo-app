const socket = io('http://192.168.4.1:5000')

const tempDiv = document.getElementById('temperatura')
const humDiv = document.getElementById('humedad')
const distDiv = document.getElementById('distancia')
const volumenDiv = document.getElementById('volumen')

// ✅ Arrays
const datosTemperatura = []
const datosHumedad = []
const datosDistancia = []
const datosVolumen = []
const etiquetas = []

// Parámetros silo
const ALTURA_SILO = 1.0
const RADIO_SILO = 0.05  // ✅ CORREGIDO a 5 cm

// ✅ Gráfico temperatura
const ctxTemp = document.getElementById('graficoTemp').getContext('2d')
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
})

// ✅ Gráfico humedad
const ctxHum = document.getElementById('graficoHum').getContext('2d')
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
})

// ✅ Gráfico volumen
const ctxVol = document.getElementById('graficoVol').getContext('2d')
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
})

// ✅ MQTT: Recibir datos en vivo
socket.on('nuevos_datos', data => {
  const now = new Date().toLocaleTimeString()

  etiquetas.push(now)
  datosTemperatura.push(Number(data.temperatura))
  datosHumedad.push(Number(data.humedad))
  datosDistancia.push(Number(data.distancia))

  // Convertir distancia a metros
  const distEnMetros = Number(data.distancia) / 100
  const alturaMaterial = ALTURA_SILO - distEnMetros
  const volumen = Math.PI * Math.pow(RADIO_SILO, 2) * alturaMaterial
  datosVolumen.push(volumen.toFixed(2))

  if (etiquetas.length > 20) {
    etiquetas.shift()
    datosTemperatura.shift()
    datosHumedad.shift()
    datosDistancia.shift()
    datosVolumen.shift()
  }

  tempDiv.innerText = data.temperatura + " °C"
  humDiv.innerText = data.humedad + " %"
  distDiv.innerText = data.distancia + " cm"
  volumenDiv.innerText = volumen.toFixed(2) + " m³"

  chartTemp.update()
  chartHum.update()
  chartVol.update()
})

// ✅ Enviar datos manuales (local)
document.getElementById('enviar-param').addEventListener('click', () => {
  const temp = document.getElementById('input-temp').value
  const hum = document.getElementById('input-hum').value
  const dist = document.getElementById('input-dist').value

  const ultimaTemp = datosTemperatura.length ? datosTemperatura[datosTemperatura.length - 1] : 0
  const ultimaHum = datosHumedad.length ? datosHumedad[datosHumedad.length - 1] : 0
  const ultimaDist = datosDistancia.length ? datosDistancia[datosDistancia.length - 1] : 0
  const ultimaVol = datosVolumen.length ? datosVolumen[datosVolumen.length - 1] : 0

  const nuevaTemp = temp !== '' ? Number(temp) : ultimaTemp
  const nuevaHum = hum !== '' ? Number(hum) : ultimaHum
  const nuevaDist = dist !== '' ? Number(dist) : ultimaDist

  // Convertir distancia a metros
  const distEnMetros = nuevaDist / 100
  const alturaMaterial = ALTURA_SILO - distEnMetros
  const nuevoVolumen = Math.PI * Math.pow(RADIO_SILO, 2) * alturaMaterial

  const now = new Date().toLocaleTimeString()

  etiquetas.push(now)
  datosTemperatura.push(nuevaTemp)
  datosHumedad.push(nuevaHum)
  datosDistancia.push(nuevaDist)
  datosVolumen.push(nuevoVolumen.toFixed(2))

  if (etiquetas.length > 20) {
    etiquetas.shift()
    datosTemperatura.shift()
    datosHumedad.shift()
    datosDistancia.shift()
    datosVolumen.shift()
  }

  tempDiv.innerText = nuevaTemp + " °C"
  humDiv.innerText = nuevaHum + " %"
  distDiv.innerText = nuevaDist + " cm"
  volumenDiv.innerText = nuevoVolumen.toFixed(2) + " m³"

  chartTemp.update()
  chartHum.update()
  chartVol.update()

  // ✅ Modal
  const modal = document.getElementById('modal')
  modal.style.display = "block"

  document.getElementById('modal-close').onclick = function() {
    modal.style.display = "none"
  }

  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none"
    }
  }
})
