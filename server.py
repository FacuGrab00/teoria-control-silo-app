import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

humedad_actual = "N/D"

# Conexión a la base de datos SQLite
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# Función para guardar humedad en la base de datos
def guardar_humedad(valor):
    cursor.execute("INSERT INTO humedad (valor) VALUES (?)", (valor,))
    conn.commit()

# MQTT: conectado al broker
def on_connect(client, userdata, flags, rc, properties=None):
    print("Conectado al broker MQTT. Código:", rc)
    client.subscribe("sensor/humedad")

# MQTT: cuando llega un mensaje
def on_message(client, userdata, msg):
    global humedad_actual
    humedad_actual = msg.payload.decode()
    print(f"Humedad recibida: {humedad_actual}")

    guardar_humedad(humedad_actual)
    socketio.emit('nueva_humedad', {'valor': humedad_actual})

# Configurar cliente MQTT
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/humedad")
def get_humedad():
    return jsonify({"humedad": humedad_actual})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
