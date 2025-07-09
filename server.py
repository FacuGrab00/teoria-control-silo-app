import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

datos_sensores = {
    "humedad": "N/D",
    "temperatura": "N/D",
    "distancia": "N/D"
}

# MQTT
def on_connect(client, userdata, flags, rc, properties=None):
    print("Conectado al broker MQTT. Código:", rc)
    client.subscribe("sensor/#")  # Escucha todos los sensores

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    topic = msg.topic

    print(f"Mensaje en {topic}: {payload}")

    if topic == "sensor/dht22":
        # Se espera un JSON tipo: {"temperatura": 22.3, "humedad": 55.1}
        import json
        try:
            data = json.loads(payload)
            datos_sensores["temperatura"] = data["temperatura"]
            datos_sensores["humedad"] = data["humedad"]
        except Exception as e:
            print("Error parseando dht22:", e)

    elif topic == "sensor/distancia":
        import json
        try:
            data = json.loads(payload)
            datos_sensores["distancia"] = data["distancia"]
        except Exception as e:
            print("Error parseando distancia:", e)

    socketio.emit('nuevos_datos', datos_sensores)

# MQTT Config
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)