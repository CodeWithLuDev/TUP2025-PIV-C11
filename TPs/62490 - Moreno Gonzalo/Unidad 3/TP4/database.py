import sqlite3
from contextlib import contextmanager

# ============== CONFIGURACIÓN ==============

DB_NAME = "tareas.db"

# ============== CONTEXT MANAGER ==============

@contextmanager
def get_db_connection():
    """
    Context manager para manejar conexiones a la base de datos.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ============== INICIALIZACIÓN ==============

def init_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    with get_db_connection() as conn:
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
        
        # Tabla tareas con clave foránea
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                proyecto_id INTEGER NOT NULL,
                fecha_creacion TEXT NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()

# ============== FUNCIONES AUXILIARES ==============

def row_to_dict(row):
    """
    Convierte un objeto sqlite3.Row en un diccionario.
    """
    return dict(row) if row else None