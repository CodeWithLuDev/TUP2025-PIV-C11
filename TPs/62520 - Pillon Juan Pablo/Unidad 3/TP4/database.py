import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tareas.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # activar claves foraneas
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """
    Crea/reinicia las tablas. Garantiza un estado limpio incluso si
    init_db() se llama al importar la app (TestClient al inicio).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Eliminar tablas si existen (asegura DB limpia)
    cur.execute("DROP TABLE IF EXISTS tareas;")
    cur.execute("DROP TABLE IF EXISTS proyectos;")

    # crear tabla proyectos
    cur.execute("""
    CREATE TABLE proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    );
    """)
    # crear tabla tareas con FK y ON DELETE CASCADE
    cur.execute("""
    CREATE TABLE tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        prioridad TEXT NOT NULL,
        proyecto_id INTEGER,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()