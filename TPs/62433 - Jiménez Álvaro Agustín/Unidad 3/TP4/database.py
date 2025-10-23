import sqlite3
from contextlib import contextmanager
from typing import Optional, List
from datetime import datetime

DB_NAME = "tareas.db"

@contextmanager
def get_db():
    """Context manager para conexiones a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Habilitar claves foráneas
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Crear tabla proyectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        
        # Crear tabla tareas con relación a proyectos
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

# ============ FUNCIONES DE PROYECTOS ============

def crear_proyecto(nombre: str, descripcion: Optional[str] = None):
    """Crea un nuevo proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        try:
            cursor.execute(
                "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
                (nombre, descripcion, fecha_creacion)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Nombre duplicado

def obtener_proyecto(proyecto_id: int):
    """Obtiene un proyecto por ID con contador de tareas"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (proyecto_id,))
        return cursor.fetchone()

def obtener_proyectos(nombre: Optional[str] = None):
    """Obtiene todos los proyectos con contador de tareas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
        """
        params = []
        
        if nombre:
            query += " WHERE p.nombre LIKE ?"
            params.append(f"%{nombre}%")
        
        query += " GROUP BY p.id ORDER BY p.fecha_creacion DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

def actualizar_proyecto(proyecto_id: int, nombre: Optional[str], descripcion: Optional[str]):
    """Actualiza un proyecto existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            return None
        
        updates = []
        params = []
        
        if nombre is not None:
            updates.append("nombre = ?")
            params.append(nombre)
        
        if descripcion is not None:
            updates.append("descripcion = ?")
            params.append(descripcion)
        
        if not updates:
            return proyecto_id
        
        params.append(proyecto_id)
        query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return proyecto_id
        except sqlite3.IntegrityError:
            return False  # Nombre duplicado

def eliminar_proyecto(proyecto_id: int):
    """Elimina un proyecto y sus tareas (CASCADE)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            return False
        
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        conn.commit()
        return True

# ============ FUNCIONES DE TAREAS ============

def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int):
    """Crea una nueva tarea"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            return None
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
            (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        )
        conn.commit()
        return cursor.lastrowid

def obtener_tarea(tarea_id: int):
    """Obtiene una tarea por ID con nombre del proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, p.nombre as proyecto_nombre
            FROM tareas t
            JOIN proyectos p ON t.proyecto_id = p.id
            WHERE t.id = ?
        """, (tarea_id,))
        return cursor.fetchone()

def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None, 
                   prioridad: Optional[str] = None, proyecto_id: Optional[int] = None,
                   orden: Optional[str] = None):
    """Obtiene todas las tareas con filtros opcionales"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, p.nombre as proyecto_nombre
            FROM tareas t
            JOIN proyectos p ON t.proyecto_id = p.id
            WHERE 1=1
        """
        params = []
        
        if estado:
            query += " AND t.estado = ?"
            params.append(estado)
        
        if texto:
            query += " AND t.descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            query += " AND t.prioridad = ?"
            params.append(prioridad)
        
        if proyecto_id:
            query += " AND t.proyecto_id = ?"
            params.append(proyecto_id)
        
        if orden and orden.lower() in ["asc", "desc"]:
            query += f" ORDER BY t.fecha_creacion {orden.upper()}"
        else:
            query += " ORDER BY t.id"
        
        cursor.execute(query, params)
        return cursor.fetchall()

def obtener_tareas_por_proyecto(proyecto_id: int, estado: Optional[str] = None,
                                 prioridad: Optional[str] = None, orden: Optional[str] = None):
    """Obtiene todas las tareas de un proyecto específico"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            return None
        
        query = """
            SELECT t.*, p.nombre as proyecto_nombre
            FROM tareas t
            JOIN proyectos p ON t.proyecto_id = p.id
            WHERE t.proyecto_id = ?
        """
        params = [proyecto_id]
        
        if estado:
            query += " AND t.estado = ?"
            params.append(estado)
        
        if prioridad:
            query += " AND t.prioridad = ?"
            params.append(prioridad)
        
        if orden and orden.lower() in ["asc", "desc"]:
            query += f" ORDER BY t.fecha_creacion {orden.upper()}"
        else:
            query += " ORDER BY t.id"
        
        cursor.execute(query, params)
        return cursor.fetchall()

def actualizar_tarea(tarea_id: int, descripcion: Optional[str], estado: Optional[str],
                     prioridad: Optional[str], proyecto_id: Optional[int]):
    """Actualiza una tarea existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        tarea = cursor.fetchone()
        if not tarea:
            return None
        
        # Si se cambia el proyecto, verificar que existe
        if proyecto_id is not None:
            cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
            if not cursor.fetchone():
                return False  # Proyecto no existe
        
        updates = []
        params = []
        
        if descripcion is not None:
            updates.append("descripcion = ?")
            params.append(descripcion)
        
        if estado is not None:
            updates.append("estado = ?")
            params.append(estado)
        
        if prioridad is not None:
            updates.append("prioridad = ?")
            params.append(prioridad)
        
        if proyecto_id is not None:
            updates.append("proyecto_id = ?")
            params.append(proyecto_id)
        
        if not updates:
            return tarea_id
        
        params.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        return tarea_id

def eliminar_tarea(tarea_id: int):
    """Elimina una tarea"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if not cursor.fetchone():
            return False
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        return True

# ============ FUNCIONES DE ESTADÍSTICAS ============

def obtener_resumen_proyecto(proyecto_id: int):
    """Obtiene estadísticas de un proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
        proyecto = cursor.fetchone()
        if not proyecto:
            return None
        
        # Contar tareas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY estado
        """, (proyecto_id,))
        
        por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            por_estado[row["estado"]] = row["cantidad"]
        
        # Contar tareas por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY prioridad
        """, (proyecto_id,))
        
        por_prioridad = {"baja": 0, "media": 0, "alta": 0}
        for row in cursor.fetchall():
            por_prioridad[row["prioridad"]] = row["cantidad"]
        
        total_tareas = sum(por_estado.values())
        
        return {
            "proyecto_id": proyecto_id,
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

def obtener_resumen_general():
    """Obtiene estadísticas generales de toda la aplicación"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total de proyectos
        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()["total"]
        
        # Total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Tareas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        
        tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            tareas_por_estado[row["estado"]] = row["cantidad"]
        
        # Proyecto con más tareas
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        
        proyecto_top = cursor.fetchone()
        proyecto_con_mas_tareas = None
        if proyecto_top and proyecto_top["cantidad_tareas"] > 0:
            proyecto_con_mas_tareas = {
                "id": proyecto_top["id"],
                "nombre": proyecto_top["nombre"],
                "cantidad_tareas": proyecto_top["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }