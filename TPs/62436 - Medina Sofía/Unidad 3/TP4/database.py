import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_NAME = "tareas.db"

def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db_connection()
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

# ==================== FUNCIONES DE PROYECTOS ====================

def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> Dict[str, Any]:
    """Crea un nuevo proyecto en la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (nombre, descripcion, fecha_creacion))
        conn.commit()
        proyecto_id = cursor.lastrowid
        
        return {
            "id": proyecto_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "fecha_creacion": fecha_creacion
        }
    except sqlite3.IntegrityError:
        raise ValueError("Ya existe un proyecto con ese nombre")
    finally:
        conn.close()

def obtener_proyectos(nombre: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los proyectos o filtra por nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute("""
            SELECT * FROM proyectos 
            WHERE nombre LIKE ?
            ORDER BY fecha_creacion DESC
        """, (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos ORDER BY fecha_creacion DESC")
    
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return proyectos

def obtener_proyecto_por_id(proyecto_id: int, incluir_contador: bool = False) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    proyecto = dict(row)
    
    if incluir_contador:
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        total = cursor.fetchone()["total"]
        proyecto["total_tareas"] = total
    
    conn.close()
    return proyecto

def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un proyecto existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Construir query de actualización
    campos = []
    valores = []
    
    if nombre is not None:
        campos.append("nombre = ?")
        valores.append(nombre)
    if descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(descripcion)
    
    if not campos:
        conn.close()
        return obtener_proyecto_por_id(proyecto_id)
    
    valores.append(proyecto_id)
    query = f"UPDATE proyectos SET {', '.join(campos)} WHERE id = ?"
    
    try:
        cursor.execute(query, valores)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Ya existe un proyecto con ese nombre")
    
    conn.close()
    return obtener_proyecto_por_id(proyecto_id)

def eliminar_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Elimina un proyecto y todas sus tareas asociadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_eliminadas = cursor.fetchone()["total"]
    
    # Eliminar proyecto (CASCADE eliminará las tareas)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Proyecto eliminado", "tareas_eliminadas": tareas_eliminadas}

# ==================== FUNCIONES DE TAREAS ====================

def crear_tarea(proyecto_id: int, descripcion: str, estado: str = "pendiente", 
                prioridad: str = "media") -> Dict[str, Any]:
    """Crea una nueva tarea en un proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("El proyecto no existe")
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (descripcion, estado, prioridad, proyecto_id, fecha_creacion))
    
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
                   prioridad: Optional[str] = None, orden: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene tareas con filtros opcionales"""
    conn = get_db_connection()
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
    
    # Ordenamiento
    if orden and orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                     estado: Optional[str] = None, prioridad: Optional[str] = None,
                     proyecto_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Si se cambia el proyecto, verificar que existe
    if proyecto_id is not None:
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError("El proyecto destino no existe")
    
    # Construir query de actualización
    campos = []
    valores = []
    
    if descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(descripcion)
    if estado is not None:
        campos.append("estado = ?")
        valores.append(estado)
    if prioridad is not None:
        campos.append("prioridad = ?")
        valores.append(prioridad)
    if proyecto_id is not None:
        campos.append("proyecto_id = ?")
        valores.append(proyecto_id)
    
    if not campos:
        conn.close()
        return obtener_tarea_por_id(tarea_id)
    
    valores.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
    
    cursor.execute(query, valores)
    conn.commit()
    conn.close()
    
    return obtener_tarea_por_id(tarea_id)

def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0

#  FUNCIONES DE ESTADÍSTICAS 

def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene estadísticas de un proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        return None
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    # Agrupar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY estado
    """, (proyecto_id,))
    por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    # Asegurar que todos los estados existen
    for estado in ["pendiente", "en_progreso", "completada"]:
        if estado not in por_estado:
            por_estado[estado] = 0
    
    # Agrupar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ? 
        GROUP BY prioridad
    """, (proyecto_id,))
    por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
    
    # Asegurar que todas las prioridades existen
    for prioridad in ["baja", "media", "alta"]:
        if prioridad not in por_prioridad:
            por_prioridad[prioridad] = 0
    
    conn.close()
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

def obtener_resumen_general() -> Dict[str, Any]:
    """Obtiene estadísticas generales de toda la aplicación"""
    conn = get_db_connection()
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
    tareas_por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    # Asegurar que todos los estados existen
    for estado in ["pendiente", "en_progreso", "completada"]:
        if estado not in tareas_por_estado:
            tareas_por_estado[estado] = 0
    
    # Proyecto con más tareas
    proyecto_con_mas_tareas = None
    if total_proyectos > 0:
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            proyecto_con_mas_tareas = {
                "id": row["id"],
                "nombre": row["nombre"],
                "cantidad_tareas": row["cantidad_tareas"]
            }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }