import sqlite3

DB_NAME = "tareas.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla proyectos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    )
    """)

    # Tabla tareas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        prioridad TEXT NOT NULL,
        proyecto_id INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY(proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()