from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Literal
import datetime
import sqlite3
from pydantic import BaseModel, Field, field_validator
from models import (
    ProyectoCreate, TareaCreate, TareaUpdate,
    ResumenEstado, ResumenPrioridad
)

# Database setup
DB_NAME = "tareas.db"

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inicializa la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion DATETIME NOT NULL
        )
    """)
    
    # Tabla tareas (modificada con proyecto_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion DATETIME NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

# Pydantic models
class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("nombre no puede estar vacío")
        return v.strip()

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    prioridad: Optional[Literal["baja", "media", "alta"]] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("descripcion no puede estar vacía")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

estadosValidos = {"pendiente", "en_progreso", "completada"}
prioridadesValidas = {"baja", "media", "alta"}

app = FastAPI()

# Inicializar DB al arrancar
init_db()

@app.get("/")
async def Bienvenida():
    return {
        "nombre": "API de Tareas y Proyectos",
        "version": "2.0",
        "endpoints": {
            "GET /proyectos": "Obtener todos los proyectos",
            "POST /proyectos": "Crear un nuevo proyecto",
            "GET /proyectos/{id}": "Obtener un proyecto específico",
            "PUT /proyectos/{id}": "Actualizar un proyecto",
            "DELETE /proyectos/{id}": "Eliminar un proyecto",
            "GET /proyectos/{id}/tareas": "Obtener tareas de un proyecto",
            "POST /proyectos/{id}/tareas": "Crear tarea en un proyecto",
            "GET /proyectos/{id}/resumen": "Obtener resumen de un proyecto",
            "GET /tareas": "Obtener todas las tareas",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /resumen": "Obtener resumen general"
        }
    }

# ============== ENDPOINTS DE PROYECTOS ==============

@app.get("/proyectos")
async def ListarProyectos(nombre: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []
    
    if nombre:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    cursor.execute(query, params)
    proyectos = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": p["id"],
            "nombre": p["nombre"],
            "descripcion": p["descripcion"],
            "fecha_creacion": p["fecha_creacion"]
        }
        for p in proyectos
    ]

@app.post("/proyectos", status_code=201)
async def CrearProyecto(proyecto: ProyectoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar nombre duplicado
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    
    fecha_creacion = datetime.datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha_creacion)
    )
    conn.commit()
    
    proyecto_id = cursor.lastrowid
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    nuevo_proyecto = cursor.fetchone()
    conn.close()
    
    return {
        "id": nuevo_proyecto["id"],
        "nombre": nuevo_proyecto["nombre"],
        "descripcion": nuevo_proyecto["descripcion"],
        "fecha_creacion": nuevo_proyecto["fecha_creacion"]
    }

@app.get("/proyectos/{id}")
async def ObtenerProyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Contar tareas
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "id": proyecto["id"],
        "nombre": proyecto["nombre"],
        "descripcion": proyecto["descripcion"],
        "fecha_creacion": proyecto["fecha_creacion"],
        "total_tareas": total_tareas
    }

@app.put("/proyectos/{id}")
async def ActualizarProyecto(id: int, proyecto: ProyectoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar nombre duplicado (excluyendo el proyecto actual)
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (proyecto.nombre, id))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    
    cursor.execute(
        "UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?",
        (proyecto.nombre, proyecto.descripcion, id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_actualizado = cursor.fetchone()
    conn.close()
    
    return {
        "id": proyecto_actualizado["id"],
        "nombre": proyecto_actualizado["nombre"],
        "descripcion": proyecto_actualizado["descripcion"],
        "fecha_creacion": proyecto_actualizado["fecha_creacion"]
    }

@app.delete("/proyectos/{id}")
async def EliminarProyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_eliminadas = cursor.fetchone()["count"]
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Proyecto eliminado",
        "tareas_eliminadas": tareas_eliminadas
    }

# ============== ENDPOINTS DE TAREAS ==============

@app.get("/proyectos/{id}/tareas")
async def ListarTareasDeProyecto(
    id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [id]
    
    if estado:
        if estado not in estadosValidos:
            conn.close()
            raise HTTPException(status_code=400, detail="Estado inválido")
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        if prioridad not in prioridadesValidas:
            conn.close()
            raise HTTPException(status_code=400, detail="Prioridad inválida")
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": t["id"],
            "descripcion": t["descripcion"],
            "estado": t["estado"],
            "prioridad": t["prioridad"],
            "proyecto_id": t["proyecto_id"],
            "fecha_creacion": t["fecha_creacion"]
        }
        for t in tareas
    ]

@app.post("/proyectos/{id}/tareas", status_code=201)
async def CrearTareaEnProyecto(id: int, tarea: TareaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Proyecto no encontrado")
    
    fecha_creacion = datetime.datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
    )
    conn.commit()
    
    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return {
        "id": nueva_tarea["id"],
        "descripcion": nueva_tarea["descripcion"],
        "estado": nueva_tarea["estado"],
        "prioridad": nueva_tarea["prioridad"],
        "proyecto_id": nueva_tarea["proyecto_id"],
        "fecha_creacion": nueva_tarea["fecha_creacion"]
    }

@app.get("/tareas")
async def ListarTodasLasTareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        if estado not in estadosValidos:
            conn.close()
            raise HTTPException(status_code=400, detail="Estado inválido")
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        if prioridad not in prioridadesValidas:
            conn.close()
            raise HTTPException(status_code=400, detail="Prioridad inválida")
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id is not None:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": t["id"],
            "descripcion": t["descripcion"],
            "estado": t["estado"],
            "prioridad": t["prioridad"],
            "proyecto_id": t["proyecto_id"],
            "fecha_creacion": t["fecha_creacion"]
        }
        for t in tareas
    ]

@app.put("/tareas/{id}")
async def ActualizarTarea(id: int, tarea_update: TareaUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Preparar valores actualizados
    descripcion = tarea_update.descripcion if tarea_update.descripcion else tarea["descripcion"]
    estado = tarea_update.estado if tarea_update.estado else tarea["estado"]
    prioridad = tarea_update.prioridad if tarea_update.prioridad else tarea["prioridad"]
    proyecto_id = tarea_update.proyecto_id if tarea_update.proyecto_id is not None else tarea["proyecto_id"]
    
    # Validar descripción
    if descripcion and not descripcion.strip():
        descripcion = tarea["descripcion"]
    
    # Validar proyecto_id si se está cambiando
    if tarea_update.proyecto_id is not None and tarea_update.proyecto_id != tarea["proyecto_id"]:
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (tarea_update.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Proyecto no encontrado")
    
    cursor.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ? WHERE id = ?",
        (descripcion, estado, prioridad, proyecto_id, id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return {
        "id": tarea_actualizada["id"],
        "descripcion": tarea_actualizada["descripcion"],
        "estado": tarea_actualizada["estado"],
        "prioridad": tarea_actualizada["prioridad"],
        "proyecto_id": tarea_actualizada["proyecto_id"],
        "fecha_creacion": tarea_actualizada["fecha_creacion"]
    }

@app.delete("/tareas/{id}")
async def EliminarTarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}

# ============== ENDPOINTS DE RESUMEN ==============

@app.get("/proyectos/{id}/resumen")
async def ResumenProyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()["count"]
    
    # Por estado
    resumen_estado = {estado: 0 for estado in estadosValidos}
    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY estado", (id,))
    for row in cursor.fetchall():
        if row["estado"] in resumen_estado:
            resumen_estado[row["estado"]] = row["count"]
    
    # Por prioridad
    resumen_prioridad = {prioridad: 0 for prioridad in prioridadesValidas}
    cursor.execute("SELECT prioridad, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (id,))
    for row in cursor.fetchall():
        if row["prioridad"] in resumen_prioridad:
            resumen_prioridad[row["prioridad"]] = row["count"]
    
    conn.close()
    
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": resumen_estado,
        "por_prioridad": resumen_prioridad
    }

@app.get("/resumen")
async def ResumenGeneral():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total proyectos
    cursor.execute("SELECT COUNT(*) as count FROM proyectos")
    total_proyectos = cursor.fetchone()["count"]
    
    # Total tareas
    cursor.execute("SELECT COUNT(*) as count FROM tareas")
    total_tareas = cursor.fetchone()["count"]
    
    # Tareas por estado
    tareas_por_estado = {estado: 0 for estado in estadosValidos}
    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado")
    for row in cursor.fetchall():
        if row["estado"] in tareas_por_estado:
            tareas_por_estado[row["estado"]] = row["count"]
    
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
        proyecto = cursor.fetchone()
        if proyecto:
            proyecto_con_mas_tareas = {
                "id": proyecto["id"],
                "nombre": proyecto["nombre"],
                "cantidad_tareas": proyecto["cantidad_tareas"]
            }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }