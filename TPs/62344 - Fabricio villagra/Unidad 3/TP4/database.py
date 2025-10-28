import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime


DB_NAME = "tareas.db"


def get_connection():
    """Devuelve una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Habilitar claves foráneas (importante para ON DELETE CASCADE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla de proyectos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de tareas con relación a proyectos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()


# ============== FUNCIONES DE PROYECTOS ==============

def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> Dict[str, Any]:
    """Crea un nuevo proyecto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    ''', (nombre, descripcion, fecha_creacion))
    
    conn.commit()
    proyecto_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": proyecto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "fecha_creacion": fecha_creacion
    }


def obtener_proyectos(nombre: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los proyectos con filtro opcional por nombre"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []
    
    if nombre:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    proyectos = cursor.fetchall()
    conn.close()
    
    return [dict(proyecto) for proyecto in proyectos]


def obtener_proyecto_por_id(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto específico con contador de tareas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Contar tareas asociadas
    cursor.execute("SELECT COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    cantidad = cursor.fetchone()["cantidad"]
    
    conn.close()
    
    proyecto_dict = dict(proyecto)
    proyecto_dict["total_tareas"] = cantidad
    
    return proyecto_dict


def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un proyecto existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Actualizar campos proporcionados
    if nombre is not None:
        cursor.execute("UPDATE proyectos SET nombre = ? WHERE id = ?", (nombre, proyecto_id))
    
    if descripcion is not None:
        cursor.execute("UPDATE proyectos SET descripcion = ? WHERE id = ?", (descripcion, proyecto_id))
    
    conn.commit()
    
    # Obtener proyecto actualizado
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    conn.close()
    
    return dict(proyecto)


def eliminar_proyecto(proyecto_id: int) -> bool:
    """Elimina un proyecto y sus tareas (CASCADE)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    
    return True


def proyecto_existe(proyecto_id: int) -> bool:
    """Verifica si un proyecto existe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    existe = cursor.fetchone() is not None
    
    conn.close()
    return existe


def nombre_proyecto_existe(nombre: str, excluir_id: Optional[int] = None) -> bool:
    """Verifica si un nombre de proyecto ya existe"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if excluir_id:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (nombre, excluir_id))
    else:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (nombre,))
    
    existe = cursor.fetchone() is not None
    
    conn.close()
    return existe


# ============== FUNCIONES DE TAREAS ==============

def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int) -> Dict[str, Any]:
    """Crea una nueva tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    ''', (descripcion, estado, prioridad, proyecto_id, fecha_creacion))
    
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


def obtener_tareas(estado: Optional[str] = None, prioridad: Optional[str] = None,
                   proyecto_id: Optional[int] = None, orden: str = "asc") -> List[Dict[str, Any]]:
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_connection()
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
    
    if prioridad:
        query += " AND t.prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id:
        query += " AND t.proyecto_id = ?"
        params.append(proyecto_id)
    
    if orden == "desc":
        query += " ORDER BY t.fecha_creacion DESC"
    else:
        query += " ORDER BY t.fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


def obtener_tareas_por_proyecto(proyecto_id: int, estado: Optional[str] = None,
                                prioridad: Optional[str] = None, orden: str = "asc") -> List[Dict[str, Any]]:
    """Obtiene todas las tareas de un proyecto específico"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [proyecto_id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea específica"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    
    conn.close()
    
    return dict(tarea) if tarea else None


def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                    estado: Optional[str] = None, prioridad: Optional[str] = None,
                    proyecto_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Actualiza una tarea existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Actualizar campos proporcionados
    if descripcion is not None:
        cursor.execute("UPDATE tareas SET descripcion = ? WHERE id = ?", (descripcion, tarea_id))
    
    if estado is not None:
        cursor.execute("UPDATE tareas SET estado = ? WHERE id = ?", (estado, tarea_id))
    
    if prioridad is not None:
        cursor.execute("UPDATE tareas SET prioridad = ? WHERE id = ?", (prioridad, tarea_id))
    
    if proyecto_id is not None:
        cursor.execute("UPDATE tareas SET proyecto_id = ? WHERE id = ?", (proyecto_id, tarea_id))
    
    conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return dict(tarea)


def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return True


# ============== FUNCIONES DE RESUMEN ==============

def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene estadísticas de un proyecto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    # Por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    # Por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
    
    conn.close()
    
    # Asegurar que todos los estados y prioridades aparezcan
    for estado in ["pendiente", "en_progreso", "completada"]:
        if estado not in por_estado:
            por_estado[estado] = 0
    
    for prioridad in ["baja", "media", "alta"]:
        if prioridad not in por_prioridad:
            por_prioridad[prioridad] = 0
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


def obtener_resumen_general() -> Dict[str, Any]:
    """Obtiene resumen general de toda la aplicación"""
    conn = get_connection()
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
    
    # Asegurar que todos los estados aparezcan
    for estado in ["pendiente", "en_progreso", "completada"]:
        if estado not in tareas_por_estado:
            tareas_por_estado[estado] = 0
    
    # Proyecto con más tareas
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    proyecto_mas_tareas = cursor.fetchone()
    
    conn.close()
    
    resultado = {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado
    }
    
    if proyecto_mas_tareas and proyecto_mas_tareas["cantidad_tareas"] > 0:
        resultado["proyecto_con_mas_tareas"] = {
            "id": proyecto_mas_tareas["id"],
            "nombre": proyecto_mas_tareas["nombre"],
            "cantidad_tareas": proyecto_mas_tareas["cantidad_tareas"]
        }
    else:
        resultado["proyecto_con_mas_tareas"] = None
    
    return resultado