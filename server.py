import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import math
import RPi.GPIO as GPIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Datos
datos_sensores = {
    "humedad": "N/D",
    "temperatura": "N/D",
    "distancia": "N/D",
    "volumen": "N/D"
}

# Parámetros
ALTURA_SILO = 1.0 
RADIO_SILO = 0.05      
UMBRAL_HUMEDAD = 50

# GPIO setup
GPIO.setmode(GPIO.BCM)
PIN_RELE = 17
GPIO.setup(PIN_RELE, GPIO.OUT)
GPIO.output(PIN_RELE, GPIO.LOW)

# MQTT callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Conectado MQTT. Código:", rc)
    client.subscribe("sensor/#")

def controlar_ventilador(humedad):
    if humedad >= UMBRAL_HUMEDAD:
        GPIO.output(PIN_RELE, GPIO.HIGH)
        print("💨 Ventilador ENCENDIDO")
    else:
        GPIO.output(PIN_RELE, GPIO.LOW)
        print("💨 Ventilador APAGADO")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    topic = msg.topic

    try:
        data = json.loads(payload)
    except Exception as e:
        print("❌ Error JSON:", e)
        return

    if topic == "sensor/dht22":
        humedad = float(data.get("humedad", 0))
        datos_sensores["humedad"] = humedad
        datos_sensores["temperatura"] = data.get("temperatura", "N/D")

        controlar_ventilador(humedad)

    elif topic == "sensor/distancia":
        distancia = float(data.get("distancia", 0))
        datos_sensores["distancia"] = distancia

        altura_material = ALTURA_SILO - (distancia / 100)
        if altura_material < 0:
            altura_material = 0

        area_base = math.pi * RADIO_SILO**2
        volumen = area_base * altura_material
        datos_sensores["volumen"] = round(volumen, 2)

    socketio.emit('nuevos_datos', datos_sensores)

client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

@app.route('/')
def index():
    return render_template("index.html")

@socketio.on('parametros_actualizados')
def manejar_parametros(data):
    try:
        humedad = float(data.get("humedad", 0))
        controlar_ventilador(humedad)
        print(f"💻 Humedad manual recibida: {humedad}")
    except Exception as e:
        print("❌ Error humedad manual:", e)

if __name__ == "__main__":
    try:
        print("🚀 Servidor Flask + SocketIO iniciado en 0.0.0.0:5000")
        socketio.run(app, host="0.0.0.0", port=5000)
    finally:
        GPIO.cleanup()
