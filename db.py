import sqlite3

conn = sqlite3.connect('sensores.db')
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

CREATE INDEX IF NOT EXISTS idx_sensor ON sensores(sensor);
CREATE INDEX IF NOT EXISTS idx_tipo ON sensores(tipo);
CREATE INDEX IF NOT EXISTS idx_timestamp ON sensores(timestamp);
""")

conn.commit()
conn.close()

print("Base de datos y tabla creadas correctamente.")
