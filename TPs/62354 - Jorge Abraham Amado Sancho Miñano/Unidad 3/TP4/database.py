import sqlite3
from datetime import datetime
from typing import Generator

DB_NAME = "tareas.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Habilitar claves foráneas en cada conexión
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    """Crea las tablas proyectos y tareas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla proyectos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    );
    """)

    # Tabla tareas con clave foránea a proyectos (ON DELETE CASCADE)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
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