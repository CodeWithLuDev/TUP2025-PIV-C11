# database.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("tareas.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # MUY IMPORTANTE: activar foreign keys en cada conexión
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabla PROYECTOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre          TEXT NOT NULL UNIQUE,
        descripcion     TEXT,
        fecha_creacion  TEXT NOT NULL
    );
    """)

    # Tabla TAREAS (1:N con PROYECTOS) + ON DELETE CASCADE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion     TEXT NOT NULL,
        estado          TEXT NOT NULL,
        prioridad       TEXT NOT NULL,
        proyecto_id     INTEGER NOT NULL,
        fecha_creacion  TEXT NOT NULL,
        FOREIGN KEY (proyecto_id)
            REFERENCES proyectos(id)
            ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
