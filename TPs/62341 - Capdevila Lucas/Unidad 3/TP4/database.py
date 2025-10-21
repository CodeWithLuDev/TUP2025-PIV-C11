"""
TP4: Funciones de acceso a base de datos SQLite
"""

import sqlite3
from typing import Dict, List, Optional, Any

DB_NAME = "tareas.db"


def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        # Habilitar modo WAL para mejor concurrencia
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")  # Habilitar claves foráneas
        
        # Tabla de proyectos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        
        # Tabla de tareas con relación a proyectos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                proyecto_id INTEGER NOT NULL,
                fecha_creacion TEXT NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()


def dict_from_row(cursor, row) -> Dict[str, Any]:
    """Convierte una fila de SQLite a diccionario"""
    return {description[0]: row[i] for i, description in enumerate(cursor.description)}


def get_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ========== FUNCIONES DE PROYECTOS ==========

def crear_proyecto(nombre: str, descripcion: Optional[str], fecha_creacion: str) -> Optional[Dict]:
    """Crea un nuevo proyecto en la base de datos"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
                (nombre, descripcion, fecha_creacion)
            )
            proyecto_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
            row = cursor.fetchone()
            if row:
                proyecto = dict_from_row(cursor, row)
                proyecto['total_tareas'] = 0
                return proyecto
            return None
    except sqlite3.IntegrityError:
        return None  # Nombre duplicado


def obtener_proyectos(filtro_nombre: Optional[str] = None) -> List[Dict]:
    """Obtiene todos los proyectos con contador de tareas"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if filtro_nombre:
            query = """
                SELECT p.*, COUNT(t.id) as total_tareas
                FROM proyectos p
                LEFT JOIN tareas t ON p.id = t.proyecto_id
                WHERE p.nombre LIKE ?
                GROUP BY p.id
                ORDER BY p.fecha_creacion DESC
            """
            cursor.execute(query, (f"%{filtro_nombre}%",))
        else:
            query = """
                SELECT p.*, COUNT(t.id) as total_tareas
                FROM proyectos p
                LEFT JOIN tareas t ON p.id = t.proyecto_id
                GROUP BY p.id
                ORDER BY p.fecha_creacion DESC
            """
            cursor.execute(query)
        
        rows = cursor.fetchall()
        return [dict_from_row(cursor, row) for row in rows]


def obtener_proyecto(proyecto_id: int) -> Optional[Dict]:
    """Obtiene un proyecto específico con contador de tareas"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """
        cursor.execute(query, (proyecto_id,))
        row = cursor.fetchone()
        return dict_from_row(cursor, row) if row else None


def actualizar_proyecto(proyecto_id: int, nombre: Optional[str], descripcion: Optional[str]) -> Optional[Dict]:
    """Actualiza un proyecto existente"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que existe
            cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
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
            
            if updates:
                query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
                params.append(proyecto_id)
                cursor.execute(query, params)
                conn.commit()
            
            return obtener_proyecto(proyecto_id)
    except sqlite3.IntegrityError:
        return None  # Nombre duplicado


def eliminar_proyecto(proyecto_id: int) -> tuple[bool, int]:
    """Elimina un proyecto y sus tareas asociadas (CASCADE). Retorna (éxito, cantidad_tareas_eliminadas)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Contar tareas antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        tareas_eliminadas = cursor.fetchone()[0]
        
        # Eliminar proyecto (CASCADE eliminará las tareas)
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        conn.commit()
        
        return (cursor.rowcount > 0, tareas_eliminadas)


# ========== FUNCIONES DE TAREAS ==========

def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int, fecha_creacion: str) -> Optional[Dict]:
    """Crea una nueva tarea asociada a un proyecto"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
                (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
            )
            tarea_id = cursor.lastrowid
            conn.commit()
            
            return obtener_tarea(tarea_id)
    except sqlite3.IntegrityError:
        return None  # proyecto_id no existe


def obtener_tareas(proyecto_id: Optional[int] = None, estado: Optional[str] = None,
                   prioridad: Optional[str] = None, orden: Optional[str] = None) -> List[Dict]:
    """Obtiene tareas con filtros opcionales"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT t.*, p.nombre as proyecto_nombre
            FROM tareas t
            JOIN proyectos p ON t.proyecto_id = p.id
        """
        
        conditions = []
        params = []
        
        if proyecto_id is not None:
            conditions.append("t.proyecto_id = ?")
            params.append(proyecto_id)
        
        if estado is not None:
            conditions.append("t.estado = ?")
            params.append(estado)
        
        if prioridad is not None:
            conditions.append("t.prioridad = ?")
            params.append(prioridad)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Ordenamiento
        if orden == "desc":
            query += " ORDER BY t.fecha_creacion DESC"
        else:
            query += " ORDER BY t.fecha_creacion ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict_from_row(cursor, row) for row in rows]


def obtener_tarea(tarea_id: int) -> Optional[Dict]:
    """Obtiene una tarea específica"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT t.*, p.nombre as proyecto_nombre
            FROM tareas t
            JOIN proyectos p ON t.proyecto_id = p.id
            WHERE t.id = ?
        """
        cursor.execute(query, (tarea_id,))
        row = cursor.fetchone()
        return dict_from_row(cursor, row) if row else None


def actualizar_tarea(tarea_id: int, descripcion: Optional[str], estado: Optional[str],
                     prioridad: Optional[str], proyecto_id: Optional[int]) -> Optional[Dict]:
    """Actualiza una tarea existente"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que existe
            cursor.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,))
            if not cursor.fetchone():
                return None
            
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
                # Verificar que el proyecto existe
                cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
                if not cursor.fetchone():
                    return None
                updates.append("proyecto_id = ?")
                params.append(proyecto_id)
            
            if updates:
                query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
                params.append(tarea_id)
                cursor.execute(query, params)
                conn.commit()
            
            return obtener_tarea(tarea_id)
    except sqlite3.IntegrityError:
        return None


def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        return cursor.rowcount > 0


# ========== FUNCIONES DE RESUMEN ==========

def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict]:
    """Obtiene estadísticas de un proyecto"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        proyecto_nombre = row[0]
        
        # Total de tareas
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        total_tareas = cursor.fetchone()[0]
        
        # Por estado
        cursor.execute(
            "SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY estado",
            (proyecto_id,)
        )
        por_estado = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Por prioridad
        cursor.execute(
            "SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
            (proyecto_id,)
        )
        por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "proyecto_id": proyecto_id,
            "proyecto_nombre": proyecto_nombre,
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }


def obtener_resumen_general() -> Dict:
    """Obtiene estadísticas generales de toda la aplicación"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total proyectos
        cursor.execute("SELECT COUNT(*) FROM proyectos")
        total_proyectos = cursor.fetchone()[0]
        
        # Total tareas
        cursor.execute("SELECT COUNT(*) FROM tareas")
        total_tareas = cursor.fetchone()[0]
        
        # Tareas por estado
        cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
        tareas_por_estado = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Proyecto con más tareas
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        proyecto_con_mas_tareas = None
        if row and row[2] > 0:
            proyecto_con_mas_tareas = {
                "id": row[0],
                "nombre": row[1],
                "cantidad_tareas": row[2]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }