import sqlite3
from datetime import datetime
from typing import Optional

# Nombre del archivo de base de datos
DATABASE_NAME = "tareas.db"


def get_db_connection():
    """
    Crea una conexión a la base de datos SQLite
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Inicializa la base de datos creando las tablas si no existen
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # TABLA PROYECTOS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # TABLA TAREAS
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
    print("✅ Base de datos inicializada correctamente")


# ==========================================
# FUNCIONES PARA PROYECTOS
# ==========================================

def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> dict:
    """
    Crea un nuevo proyecto en la base de datos
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    """, (nombre, descripcion, fecha_actual))
    
    proyecto_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": proyecto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "fecha_creacion": fecha_actual
    }


def obtener_proyectos(filtro_nombre: Optional[str] = None) -> list:
    """
    Obtiene todos los proyectos, opcionalmente filtrados por nombre
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if filtro_nombre:
        cursor.execute("""
            SELECT * FROM proyectos 
            WHERE nombre LIKE ?
            ORDER BY fecha_creacion DESC
        """, (f"%{filtro_nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos ORDER BY fecha_creacion DESC")
    
    proyectos = cursor.fetchall()
    conn.close()
    
    return [dict(proyecto) for proyecto in proyectos]


def obtener_proyecto_por_id(proyecto_id: int) -> Optional[dict]:
    """
    Obtiene un proyecto específico por su ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    conn.close()
    
    return dict(proyecto) if proyecto else None


def contar_tareas_proyecto(proyecto_id: int) -> int:
    """
    Cuenta cuántas tareas tiene un proyecto
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    resultado = cursor.fetchone()
    conn.close()
    
    return resultado["total"]


def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> bool:
    """
    Actualiza un proyecto existente
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    campos_actualizar = []
    valores = []
    
    if nombre is not None:
        campos_actualizar.append("nombre = ?")
        valores.append(nombre)
    
    if descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(descripcion)
    
    if not campos_actualizar:
        return False
    
    valores.append(proyecto_id)
    query = f"UPDATE proyectos SET {', '.join(campos_actualizar)} WHERE id = ?"
    
    cursor.execute(query, valores)
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0


def eliminar_proyecto(proyecto_id: int) -> bool:
    """
    Elimina un proyecto y todas sus tareas (gracias a ON DELETE CASCADE)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0


# ==========================================
# FUNCIONES PARA TAREAS
# ==========================================

def crear_tarea(descripcion: str, estado: str, prioridad: str, 
                proyecto_id: int) -> dict:
    """
    Crea una nueva tarea en un proyecto
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (descripcion, estado, prioridad, proyecto_id, fecha_actual))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": fecha_actual
    }


def obtener_tareas(proyecto_id: Optional[int] = None, 
                   estado: Optional[str] = None,
                   prioridad: Optional[str] = None,
                   orden: str = "desc") -> list:
    """
    Obtiene tareas con filtros opcionales
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if proyecto_id is not None:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    if estado is not None:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad is not None:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden.lower() == "asc":
        query += " ORDER BY fecha_creacion ASC"
    else:
        query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


def obtener_tarea_por_id(tarea_id: int) -> Optional[dict]:
    """
    Obtiene una tarea específica por su ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return dict(tarea) if tarea else None


def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                    estado: Optional[str] = None, prioridad: Optional[str] = None,
                    proyecto_id: Optional[int] = None) -> bool:
    """
    Actualiza una tarea existente
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    campos_actualizar = []
    valores = []
    
    if descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(descripcion)
    
    if estado is not None:
        campos_actualizar.append("estado = ?")
        valores.append(estado)
    
    if prioridad is not None:
        campos_actualizar.append("prioridad = ?")
        valores.append(prioridad)
    
    if proyecto_id is not None:
        campos_actualizar.append("proyecto_id = ?")
        valores.append(proyecto_id)
    
    if not campos_actualizar:
        return False
    
    valores.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    
    cursor.execute(query, valores)
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0


def eliminar_tarea(tarea_id: int) -> bool:
    """
    Elimina una tarea
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return filas_afectadas > 0


# ==========================================
# FUNCIONES PARA ESTADÍSTICAS
# ==========================================

def obtener_estadisticas_proyecto(proyecto_id: int) -> Optional[dict]:
    """
    Obtiene estadísticas detalladas de un proyecto
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    
    por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    
    por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


def obtener_resumen_general() -> dict:
    """
    Obtiene un resumen general de toda la aplicación
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    
    tareas_por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
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
    
    if proyecto_top:
        proyecto_con_mas_tareas = {
            "id": proyecto_top["id"],
            "nombre": proyecto_top["nombre"],
            "cantidad_tareas": proyecto_top["cantidad_tareas"]
        }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }