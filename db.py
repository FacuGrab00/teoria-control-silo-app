import sqlite3
from collections import defaultdict

conexion = None

def conectar_bd():
    global conexion
    if conexion is None:
        conexion = sqlite3.connect('sensores.db', check_same_thread=False)
    return conexion

def crear_tablas():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS sensores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sensor TEXT NOT NULL,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        unidad TEXT,
        timestamp DATETIME DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS configuraciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        estado INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS parametros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        valor REAL NOT NULL,
        unidad TEXT
    );

    CREATE TABLE IF NOT EXISTS umbrales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        valor REAL NOT NULL,
        unidad TEXT,
        estado INTEGER NOT NULL  -- 0 = desactivado, 1 = activado
    );

    CREATE INDEX IF NOT EXISTS idx_sensor ON sensores(sensor);
    CREATE INDEX IF NOT EXISTS idx_tipo ON sensores(tipo);
    CREATE INDEX IF NOT EXISTS idx_timestamp ON sensores(timestamp);
    """)
    conn.commit()

# -----------------------------
# Lecturas sensores
# -----------------------------

def insertar_lectura(sensor, tipo, valor, unidad=None):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensores (sensor, tipo, valor, unidad)
        VALUES (?, ?, ?, ?)
    """, (sensor, tipo, valor, unidad))
    conn.commit()

def obtener_ultimas_lecturas(cantidad=20):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sensor, tipo, valor, unidad, timestamp
        FROM sensores
        ORDER BY timestamp DESC
        LIMIT ?
    """, (cantidad * 3,))
    filas = cursor.fetchall()

    datos = defaultdict(list)
    for sensor, tipo, valor, unidad, ts in reversed(filas):
        datos[tipo].append({"valor": valor, "unidad": unidad, "timestamp": ts})
    return datos

# -----------------------------
# Configuraciones
# -----------------------------

def guardar_modo_ventilador(valor):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO configuraciones (nombre, estado)
        VALUES ('modo_ventilador', ?)
        ON CONFLICT(nombre) DO UPDATE SET estado=excluded.estado
    """, (valor,))
    conn.commit()

def obtener_modo_ventilador():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT estado FROM configuraciones WHERE nombre = 'modo_ventilador'")
    fila = cursor.fetchone()
    return int(fila[0]) if fila else 1  # Por defecto AUTOMATICO

# -----------------------------
# Parámetros
# -----------------------------

def guardar_parametro(nombre, valor, unidad=""):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parametros (nombre, valor, unidad)
        VALUES (?, ?, ?)
        ON CONFLICT(nombre) DO UPDATE SET valor=excluded.valor, unidad=excluded.unidad
    """, (nombre, valor, unidad))
    conn.commit()

def obtener_parametro(nombre, valor_por_defecto=0.0):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM parametros WHERE nombre = ?", (nombre,))
    fila = cursor.fetchone()
    return float(fila[0]) if fila else valor_por_defecto

# -----------------------------
# Umbrales
# -----------------------------

def guardar_umbral(nombre, valor, unidad="", estado=True):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO umbrales (nombre, valor, unidad, estado)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(nombre) DO UPDATE SET valor=excluded.valor, unidad=excluded.unidad, estado=excluded.estado
    """, (nombre, valor, unidad, int(estado)))
    conn.commit()

def obtener_umbral(nombre, valor_por_defecto=0.0):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT valor, unidad, estado FROM umbrales WHERE nombre = ?", (nombre,))
    fila = cursor.fetchone()
    if fila:
        return float(fila[0]), fila[1], bool(int(fila[2]))
    return valor_por_defecto, "", False

# -----------------------------
# Limpieza
# -----------------------------

def cerrar_conexion():
    global conexion
    if conexion:
        conexion.close()
        conexion = None

# Ejecutar al importar
crear_tablas()
print("Base de datos y tablas creadas correctamente.")
