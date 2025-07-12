import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import math
import db

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    class GPIO:
        BCM = None
        OUT = None
        HIGH = 1
        LOW = 0
        @staticmethod
        def setmode(mode):
            print("GPIO setmode mock")
        @staticmethod
        def setup(pin, mode):
            print(f"GPIO setup mock pin {pin}")
        @staticmethod
        def output(pin, state):
            print(f"GPIO output mock pin {pin}, state {state}")
        @staticmethod
        def cleanup():
            print("GPIO cleanup mock")

from enum import Enum

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

class ModoVentilador(Enum):
    AUTOMATICO = 1
    MANUAL = 2

class EstadoVentilador(Enum):
    ENCENDIDO = 1
    APAGADO = 2

# Variables globales
datos_sensores = {
    "humedad": "N/D",
    "temperatura": "N/D",
    "distancia": "N/D",
    "volumen": "N/D"
}

ALTURA_SILO = db.obtener_parametro('altura_silo', 1.0)
RADIO_SILO = db.obtener_parametro('radio_silo', 0.05)

UMBRAL_HUMEDAD, _, ACTIVO_HUMEDAD = db.obtener_umbral('humedad', 50)
UMBRAL_TEMPERATURA, _, ACTIVO_TEMPERATURA = db.obtener_umbral('temperatura', 30)
UMBRAL_VOLUMEN, _, ACTIVO_VOLUMEN = db.obtener_umbral('volumen', 0.2)

modo_ventilador_val = db.obtener_modo_ventilador()
modo_ventilador = ModoVentilador(modo_ventilador_val)

# GPIO setup
GPIO.setmode(GPIO.BCM)
PIN_RELE = 17
GPIO.setup(PIN_RELE, GPIO.OUT)
GPIO.output(PIN_RELE, GPIO.LOW)

def controlar_ventilador_automatico(humedad=None, temperatura=None, volumen=None):
    if modo_ventilador != ModoVentilador.AUTOMATICO:
        print("⚙️ Modo manual")
        return

    encender = False

    if ACTIVO_HUMEDAD and humedad is not None and humedad >= UMBRAL_HUMEDAD:
        encender = True
    if ACTIVO_TEMPERATURA and temperatura is not None and temperatura >= UMBRAL_TEMPERATURA:
        encender = True
    if ACTIVO_VOLUMEN and volumen is not None and volumen >= UMBRAL_VOLUMEN:
        encender = True

    if encender:
        GPIO.output(PIN_RELE, GPIO.HIGH)
        print("Ventilador ENCENDIDO (automático)")
    else:
        GPIO.output(PIN_RELE, GPIO.LOW)
        print("Ventilador APAGADO (automático)")

def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Conectado MQTT. Código:", rc)
    client.subscribe("sensor/#")

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
        temperatura = float(data.get("temperatura", 0))
        datos_sensores["humedad"] = humedad
        datos_sensores["temperatura"] = temperatura
        db.insertar_lectura("dht22", "humedad", humedad, "%")
        db.insertar_lectura("dht22", "temperatura", temperatura, "°C")
        controlar_ventilador_automatico(humedad=humedad, temperatura=temperatura)
    elif topic == "sensor/distancia":
        distancia = float(data.get("distancia", 0))
        datos_sensores["distancia"] = distancia

        altura_material = ALTURA_SILO - (distancia / 100)
        if altura_material < 0:
            altura_material = 0

        area_base = math.pi * RADIO_SILO**2
        volumen = area_base * altura_material
        volumen = round(volumen, 2)
        datos_sensores["volumen"] = volumen
        db.insertar_lectura("ultrasonico", "distancia", distancia, "cm")
        db.insertar_lectura("ultrasonico", "volumen", volumen, "m³")
        controlar_ventilador_automatico(volumen=volumen)

    socketio.emit('nuevos_datos', datos_sensores)

# MQTT setup
client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

@app.route('/')
def index():
    modo = modo_ventilador.name.lower()
    return render_template("index.html", active_page="inicio", modo=modo)

@app.route('/configuracion')
def configuracion():
    parametros = {
        "umbral_humedad": UMBRAL_HUMEDAD,
        "umbral_temperatura": UMBRAL_TEMPERATURA,
        "umbral_volumen": UMBRAL_VOLUMEN
    }
    umbrales = {
        "humedad": ACTIVO_HUMEDAD,
        "temperatura": ACTIVO_TEMPERATURA,
        "volumen": ACTIVO_VOLUMEN
    }
    modo = modo_ventilador.name.lower()

    return render_template("configuracion.html", 
        active_page="configuracion",
        parametros=parametros,
        umbrales=umbrales,
        modo=modo
    )

@app.route('/datos_historicos')
def datos_historicos():
    datos = db.obtener_ultimas_lecturas(20)
    return jsonify(datos)

@app.route('/parametros', methods=['GET'])
def obtener_parametros():
    return {
        "altura_silo": ALTURA_SILO,
        "radio_silo": RADIO_SILO,
        "umbral_humedad": UMBRAL_HUMEDAD,
        "umbral_temperatura": UMBRAL_TEMPERATURA,
        "umbral_volumen": UMBRAL_VOLUMEN
    }, 200

@app.route('/parametros', methods=['POST'])
def actualizar_parametros():
    global ALTURA_SILO, RADIO_SILO
    global UMBRAL_HUMEDAD, UMBRAL_TEMPERATURA, UMBRAL_VOLUMEN

    data = request.json
    if not data:
        return {"error": "Faltan datos JSON"}, 400

    if "altura_silo" in data:
        ALTURA_SILO = float(data["altura_silo"])
        db.guardar_parametro('altura_silo', ALTURA_SILO, "m")
    if "radio_silo" in data:
        RADIO_SILO = float(data["radio_silo"])
        db.guardar_parametro('radio_silo', RADIO_SILO, "m")
    if "umbral_humedad" in data:
        UMBRAL_HUMEDAD = float(data["umbral_humedad"])
        db.guardar_umbral('humedad', UMBRAL_HUMEDAD, "%", ACTIVO_HUMEDAD)
    if "umbral_temperatura" in data:
        UMBRAL_TEMPERATURA = float(data["umbral_temperatura"])
        db.guardar_umbral('temperatura', UMBRAL_TEMPERATURA, "°C", ACTIVO_TEMPERATURA)
    if "umbral_volumen" in data:
        UMBRAL_VOLUMEN = float(data["umbral_volumen"])
        db.guardar_umbral('volumen', UMBRAL_VOLUMEN, "m³", ACTIVO_VOLUMEN)

    return {
        "mensaje": "Parámetros y umbrales actualizados",
        "valores": {
            "altura_silo": ALTURA_SILO,
            "radio_silo": RADIO_SILO,
            "umbral_humedad": UMBRAL_HUMEDAD,
            "umbral_temperatura": UMBRAL_TEMPERATURA,
            "umbral_volumen": UMBRAL_VOLUMEN,
        }
    }, 200

@app.route('/umbrales', methods=['GET'])
def obtener_activacion_umbrales():
    return {
        "humedad": ACTIVO_HUMEDAD,
        "temperatura": ACTIVO_TEMPERATURA,
        "volumen": ACTIVO_VOLUMEN
    }, 200

@app.route('/umbrales', methods=['POST'])
def activar_umbrales():
    global ACTIVO_HUMEDAD, ACTIVO_TEMPERATURA, ACTIVO_VOLUMEN

    data = request.json
    if not data:
        return {"error": "Faltan datos JSON"}, 400

    if "humedad" in data:
        ACTIVO_HUMEDAD = bool(data["humedad"])
        db.guardar_umbral('humedad', UMBRAL_HUMEDAD, "%", ACTIVO_HUMEDAD)
    if "temperatura" in data:
        ACTIVO_TEMPERATURA = bool(data["temperatura"])
        db.guardar_umbral('temperatura', UMBRAL_TEMPERATURA, "°C", ACTIVO_TEMPERATURA)
    if "volumen" in data:
        ACTIVO_VOLUMEN = bool(data["volumen"])
        db.guardar_umbral('volumen', UMBRAL_VOLUMEN, "m³", ACTIVO_VOLUMEN)

    return {
        "mensaje": "Activación de umbrales actualizada",
        "activados": {
            "humedad": ACTIVO_HUMEDAD,
            "temperatura": ACTIVO_TEMPERATURA,
            "volumen": ACTIVO_VOLUMEN
        }
    }, 200

@app.route('/modo_ventilador', methods=['GET'])
def obtener_modo_ventilador():
    return {"modo": modo_ventilador.value,"nombre": modo_ventilador.name.lower()}

@app.route('/modo_ventilador', methods=['POST'])
def cambiar_modo_ventilador():
    global modo_ventilador

    data = request.json
    
    if not data or "modo" not in data:
        return {"error": "Falta campo 'modo'"}, 400

    modo_valor = data["modo"]

    # Validar que sea int
    if not isinstance(modo_valor, int):
        return {"error": "'modo' debe ser un entero"}, 400

    try:
        modo_ventilador = ModoVentilador(modo_valor)
    except ValueError:
        opciones = {e.value: e.name.lower() for e in ModoVentilador}
        return {
            "error": f"Modo inválido. Use uno de: {opciones}"
        }, 400
        
    db.guardar_modo_ventilador(modo_ventilador.value)

    GPIO.output(PIN_RELE, GPIO.LOW)
    
    return {
        "mensaje": f"Modo {modo_ventilador.name.lower()} activado",
        "modo": modo_ventilador.value
    }

@app.route('/ventilador', methods=['POST'])
def controlar_ventilador_manual():
    if modo_ventilador != ModoVentilador.MANUAL:
        return {"error": "El ventilador está en modo automático. No se puede controlar manualmente."}, 400

    data = request.json
    if not data or "estado" not in data:
        return {"error": "Falta campo 'estado'"}, 400

    estado_valor = data["estado"]

    # Validar que sea int
    if not isinstance(estado_valor, int):
        return {"error": "'estado' debe ser un entero"}, 400

    try:
        estado = EstadoVentilador(estado_valor)
    except ValueError:
        return {"error": "Valor inválido para 'estado'. Use 'encendido: 1' o 'apagado: 2'."}, 400

    if estado == EstadoVentilador.ENCENDIDO:
        GPIO.output(PIN_RELE, GPIO.HIGH)
        return {"mensaje": "Ventilador ENCENDIDO"}
    else:
        GPIO.output(PIN_RELE, GPIO.LOW)
        return {"mensaje": "Ventilador APAGADO"}


if __name__ == "__main__":
    try:
        print("🚀 Servidor Flask + SocketIO iniciado en 0.0.0.0:5000")
        socketio.run(app, host="0.0.0.0", port=5000)
    finally:
        GPIO.cleanup()
        db.cerrar_conexion()




