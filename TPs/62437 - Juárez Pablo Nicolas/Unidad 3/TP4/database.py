import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime

DB_NAME = "tareas.db"

def get_db():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas si no existen"""
    conn = get_db()
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
    
    # Crear tabla tareas con clave foránea
    cursor.execute("""
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
    conn.close()
    print("Base de datos inicializada correctamente")

# Funciones para Proyectos
def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()
    
    try:
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (nombre, descripcion, fecha_creacion)
        )
        conn.commit()
        proyecto_id = cursor.lastrowid
        conn.close()
        return {
            "id": proyecto_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "fecha_creacion": fecha_creacion
        }
    except sqlite3.IntegrityError:
        conn.close()
        return None

def obtener_proyectos(nombre_filtro: Optional[str] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    if nombre_filtro:
        cursor.execute(
            "SELECT * FROM proyectos WHERE nombre LIKE ?",
            (f"%{nombre_filtro}%",)
        )
    else:
        cursor.execute("SELECT * FROM proyectos")
    
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return proyectos

def obtener_proyecto_por_id(proyecto_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if proyecto:
        proyecto = dict(proyecto)
        # Contar tareas asociadas
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        total_tareas = cursor.fetchone()['total']
        proyecto['total_tareas'] = total_tareas
    
    conn.close()
    return proyecto

def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si existe el proyecto
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Construir query dinámicamente
    updates = []
    params = []
    
    if nombre is not None:
        updates.append("nombre = ?")
        params.append(nombre)
    if descripcion is not None:
        updates.append("descripcion = ?")
        params.append(descripcion)
    
    if not updates:
        conn.close()
        return True
    
    params.append(proyecto_id)
    query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
    
    try:
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def eliminar_proyecto(proyecto_id: int) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Funciones para Tareas
def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    fecha_creacion = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": fecha_creacion
    }

def obtener_tareas(proyecto_id: Optional[int] = None, estado: Optional[str] = None,
                   prioridad: Optional[str] = None, orden: str = "asc") -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if proyecto_id is not None:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Orden por fecha de creación
    if orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return dict(tarea) if tarea else None

def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                    estado: Optional[str] = None, prioridad: Optional[str] = None,
                    proyecto_id: Optional[int] = None) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si existe la tarea
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Si se cambia de proyecto, verificar que el nuevo proyecto existe
    if proyecto_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            return False
    
    # Construir query dinámicamente
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
        conn.close()
        return True
    
    params.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return True

def eliminar_tarea(tarea_id: int) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Funciones de Estadísticas
def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        return None
    
    # Contar tareas totales
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()['total']
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY estado
    """, (proyecto_id,))
    por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY prioridad
    """, (proyecto_id,))
    por_prioridad = {row['prioridad']: row['cantidad'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

def obtener_resumen_general() -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de proyectos
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()['total']
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()['total']
    
    # Tareas por estado
    cursor.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
    tareas_por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
    
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
    if proyecto_top and proyecto_top['cantidad_tareas'] > 0:
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