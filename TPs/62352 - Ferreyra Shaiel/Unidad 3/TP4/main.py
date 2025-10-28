from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import sqlite3
from datetime import datetime
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse,
    ResumenProyecto, ResumenGeneral
)

# Configuración
DB_NAME = "tareas.db"
app = FastAPI(title="API de Gestión de Proyectos y Tareas")


# ============== FUNCIONES DE BASE DE DATOS ==============

def get_db_connection():
    """Establece conexión con la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    conn.execute("PRAGMA foreign_keys = ON")  # Activa claves foráneas
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
            estado TEXT NOT NULL DEFAULT 'pendiente',
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


# Inicializar base de datos al arrancar
init_db()


# ============== ENDPOINTS DE PROYECTOS ==============

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
        
        conn.commit()
        proyecto_id = cursor.lastrowid
        
        # Obtener el proyecto creado
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"],
            "fecha_creacion": row["fecha_creacion"],
            "total_tareas": 0
        }
        
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )
    finally:
        conn.close()


@app.get("/proyectos", response_model=List[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None)):
    """Lista todos los proyectos con filtro opcional por nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.nombre LIKE ?
            GROUP BY p.id
        """, (f"%{nombre}%",))
    else:
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
        """)
    
    proyectos = []
    for row in cursor.fetchall():
        proyectos.append({
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"],
            "fecha_creacion": row["fecha_creacion"],
            "total_tareas": row["total_tareas"]
        })
    
    conn.close()
    return proyectos


@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, COUNT(t.id) as total_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE p.id = ?
        GROUP BY p.id
    """, (proyecto_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "descripcion": row["descripcion"],
        "fecha_creacion": row["fecha_creacion"],
        "total_tareas": row["total_tareas"]
    }


@app.put("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(proyecto_id: int, proyecto: ProyectoUpdate):
    """Actualiza un proyecto existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        # Construir query dinámica
        updates = []
        params = []
        
        if proyecto.nombre is not None:
            updates.append("nombre = ?")
            params.append(proyecto.nombre)
        
        if proyecto.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(proyecto.descripcion)
        
        if updates:
            params.append(proyecto_id)
            query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Obtener proyecto actualizado
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (proyecto_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"],
            "fecha_creacion": row["fecha_creacion"],
            "total_tareas": row["total_tareas"]
        }
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )


@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    """Elimina un proyecto y todas sus tareas (CASCADE)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_eliminadas = cursor.fetchone()["total"]
    
    # Eliminar proyecto (las tareas se eliminan automáticamente por CASCADE)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Proyecto eliminado exitosamente",
        "tareas_eliminadas": tareas_eliminadas
    }


# ============== ENDPOINTS DE TAREAS ==============

@app.post("/proyectos/{proyecto_id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="El proyecto especificado no existe"
        )
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, proyecto_id, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "proyecto_id": row["proyecto_id"],
        "fecha_creacion": row["fecha_creacion"]
    }


@app.get("/proyectos/{proyecto_id}/tareas", response_model=List[TareaResponse])
def listar_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    """Lista todas las tareas de un proyecto específico"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Construir query con filtros
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [proyecto_id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Ordenamiento
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = []
    
    for row in cursor.fetchall():
        tareas.append({
            "id": row["id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "proyecto_id": row["proyecto_id"],
            "fecha_creacion": row["fecha_creacion"]
        })
    
    conn.close()
    return tareas


@app.get("/tareas", response_model=List[TareaResponse])
def listar_todas_tareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query(None)
):
    """Lista todas las tareas de todos los proyectos con filtros opcionales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    # Ordenamiento
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = []
    
    for row in cursor.fetchall():
        tareas.append({
            "id": row["id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "proyecto_id": row["proyecto_id"],
            "fecha_creacion": row["fecha_creacion"]
        })
    
    conn.close()
    return tareas


@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Si se quiere cambiar de proyecto, verificar que existe
    if tarea.proyecto_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="El proyecto especificado no existe"
            )
    
    # Construir query dinámica
    updates = []
    params = []
    
    if tarea.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(tarea.descripcion)
    
    if tarea.estado is not None:
        updates.append("estado = ?")
        params.append(tarea.estado)
    
    if tarea.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(tarea.prioridad)
    
    if tarea.proyecto_id is not None:
        updates.append("proyecto_id = ?")
        params.append(tarea.proyecto_id)
    
    if updates:
        params.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "proyecto_id": row["proyecto_id"],
        "fecha_creacion": row["fecha_creacion"]
    }


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente"}


# ============== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==============

@app.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyecto)
def resumen_proyecto(proyecto_id: int):
    """Obtiene estadísticas detalladas de un proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Contar total de tareas
    cursor.execute("""
        SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?
    """, (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in cursor.fetchall():
        por_estado[row["estado"]] = row["cantidad"]
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for row in cursor.fetchall():
        por_prioridad[row["prioridad"]] = row["cantidad"]
    
    conn.close()
    
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


@app.get("/resumen", response_model=ResumenGeneral)
def resumen_general():
    """Obtiene resumen general de toda la aplicación"""
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
    
    proyecto_row = cursor.fetchone()
    proyecto_con_mas_tareas = None
    
    if proyecto_row and proyecto_row["cantidad_tareas"] > 0:
        proyecto_con_mas_tareas = {
            "id": proyecto_row["id"],
            "nombre": proyecto_row["nombre"],
            "cantidad_tareas": proyecto_row["cantidad_tareas"]
        }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }


# ============== ENDPOINT RAÍZ ==============

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas",
        "version": "1.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen",
            "documentacion": "/docs"
        }
    }