import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE_NAME = 'tareas.db'
DB_NAME = DATABASE_NAME  

def get_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # ← AGREGAR ESTA LÍNEA
    return conn

def init_db():
    """Inicializa las tablas de la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL CHECK(estado IN ('pendiente', 'en_progreso', 'completada')),
            prioridad TEXT NOT NULL CHECK(prioridad IN ('baja', 'media', 'alta')),
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Base de datos inicializada")


def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> int:
    """Crea un nuevo proyecto"""
    conn = get_connection()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    ''', (nombre, descripcion, fecha_creacion))
    
    proyecto_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return proyecto_id

def obtener_proyectos(nombre: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todos los proyectos con filtro opcional por nombre"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute('''
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.nombre LIKE ?
            GROUP BY p.id
        ''', (f'%{nombre}%',))
    else:
        cursor.execute('''
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
        ''')
    
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return proyectos

def obtener_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto específico con contador de tareas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, COUNT(t.id) as total_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (proyecto_id,))
    
    proyecto = cursor.fetchone()
    conn.close()
    return dict(proyecto) if proyecto else None

def actualizar_proyecto(proyecto_id: int, nombre: str, descripcion: Optional[str] = None) -> bool:
    """Actualiza un proyecto existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE proyectos
        SET nombre = ?, descripcion = ?
        WHERE id = ?
    ''', (nombre, descripcion, proyecto_id))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def eliminar_proyecto(proyecto_id: int) -> bool:
    """Elimina un proyecto (y sus tareas por CASCADE)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM proyectos WHERE id = ?', (proyecto_id,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def proyecto_existe(proyecto_id: int) -> bool:
    """Verifica si un proyecto existe"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM proyectos WHERE id = ?', (proyecto_id,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int) -> int:
    """Crea una nueva tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    ''', (descripcion, estado, prioridad, proyecto_id, fecha_creacion))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tarea_id

def obtener_tareas(
    proyecto_id: Optional[int] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: str = 'asc'
) -> List[Dict[str, Any]]:
    """Lista tareas con filtros opcionales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM tareas WHERE 1=1'
    params = []
    
    if proyecto_id:
        query += ' AND proyecto_id = ?'
        params.append(proyecto_id)
    if estado:
        query += ' AND estado = ?'
        params.append(estado)
    if prioridad:
        query += ' AND prioridad = ?'
        params.append(prioridad)
    
    orden_sql = 'ASC' if orden == 'asc' else 'DESC'
    query += f' ORDER BY fecha_creacion {orden_sql}'
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

def obtener_tarea(tarea_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea específica"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tareas WHERE id = ?', (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    return dict(tarea) if tarea else None

def actualizar_tarea(tarea_id: int, descripcion: str, estado: str, prioridad: str, proyecto_id: int) -> bool:
    """Actualiza una tarea existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
        WHERE id = ?
    ''', (descripcion, estado, prioridad, proyecto_id, tarea_id))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tareas WHERE id = ?', (tarea_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene estadísticas de un proyecto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nombre FROM proyectos WHERE id = ?', (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    ''', (proyecto_id,))
    
    por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    

    cursor.execute('''
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    ''', (proyecto_id,))
    
    por_prioridad = {row['prioridad']: row['cantidad'] for row in cursor.fetchall()}
    

    cursor.execute('SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?', (proyecto_id,))
    total_tareas = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "proyecto_id": proyecto['id'],
        "proyecto_nombre": proyecto['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

def obtener_resumen_general() -> Dict[str, Any]:
    """Obtiene estadísticas generales de la aplicación"""
    conn = get_connection()
    cursor = conn.cursor()
    

    cursor.execute('SELECT COUNT(*) as total FROM proyectos')
    total_proyectos = cursor.fetchone()['total']
    

    cursor.execute('SELECT COUNT(*) as total FROM tareas')
    total_tareas = cursor.fetchone()['total']
    
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    ''')
    tareas_por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    

    cursor.execute('''
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    ''')
    
    proyecto_top = cursor.fetchone()
    proyecto_con_mas_tareas = None
    if proyecto_top:
        proyecto_con_mas_tareas = {
            "id": proyecto_top['id'],
            "nombre": proyecto_top['nombre'],
            "cantidad_tareas": proyecto_top['cantidad_tareas']
        }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }