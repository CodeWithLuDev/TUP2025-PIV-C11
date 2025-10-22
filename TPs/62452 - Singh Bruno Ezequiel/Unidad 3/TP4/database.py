# database.py
import sqlite3
from typing import Optional

DB_NAME = "tareas.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    # Activa enforcement de foreign keys en SQLite (necesario cada conexión)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Crear tabla Proyectos primero
    cur.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    );
    """)

    # Crear tabla tareas con FK a proyectos.id y ON DELETE CASCADE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        prioridad TEXT NOT NULL,
        proyecto_id INTEGER,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY(proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
