import sqlite3

conexion = sqlite3.connect("tareas.db")
cursor =conexion.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('pendiente', 'en_progreso', 'completada')) DEFAULT 'pendiente',
    fecha_creacion TEXT DEFAULT (datetime('now', 'localtime')),
    prioridad TEXT NOT NULL CHECK(prioridad IN ('baja', 'media', 'alta')) DEFAULT 'media'
)
""")

tareas= [
    ("Preparar informe de proyecto", "pendiente", "media"),
    ("Revisar código del TP2", "en_progreso", "alta"),
    ("Completar las tablas", "pendiente", "alta"),
    ("Enviar TP3 a revisión", "completada", "baja")
]

cursor.executemany("""
INSERT INTO tareas (descripcion, estado, prioridad)
VALUES (?, ?, ?)
""", tareas)


conexion.commit()
conexion.close()

print ("Base de datos tareas.db creada exitosamente")
