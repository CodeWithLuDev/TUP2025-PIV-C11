from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import datetime
import sqlite3

# Database setup
DB_NAME = "tareas.db"

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion DATETIME NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# Pydantic models
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

class TareaIn(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("descripcion no puede estar vacía")
        return v

estadosValidos = {"pendiente", "en_progreso", "completada"}
prioridadesValidas = {"baja", "media", "alta"}

app = FastAPI()

# Inicializar DB al arrancar
init_db()

@app.get("/")
async def Bienvenida():
    return {
        "nombre": "API de Tareas",
        "version": "1.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

@app.get("/tareas")
async def VomitarTareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
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
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
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
            "fecha_creacion": t["fecha_creacion"]
        }
        for t in tareas
    ]

@app.post("/tareas", status_code=201)
async def CrearTarea(tarea_in: TareaIn):
    descripcion = tarea_in.descripcion.strip()
    if not descripcion:
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
    
    estado = tarea_in.estado or "pendiente"
    if estado not in estadosValidos:
        raise HTTPException(status_code=422, detail="Estado inválido")
    
    prioridad = tarea_in.prioridad or "media"
    if prioridad not in prioridadesValidas:
        raise HTTPException(status_code=422, detail="Prioridad inválida")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (descripcion, estado, prioridad, fecha_creacion)
    )
    conn.commit()
    
    tarea_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return {
        "id": tarea["id"],
        "descripcion": tarea["descripcion"],
        "estado": tarea["estado"],
        "prioridad": tarea["prioridad"],
        "fecha_creacion": tarea["fecha_creacion"]
    }

@app.put("/tareas/completar_todas", status_code=200)
async def CompletarTodas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM tareas")
    count = cursor.fetchone()["count"]
    
    if count == 0:
        conn.close()
        return {"mensaje": "No hay tareas"}
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.put("/tareas/{id}")
async def ModificarTarea(id: int, tarea_in: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="error: Tarea no encontrada")
    
    descripcion = tarea_in.get("descripcion", tarea["descripcion"])
    estado = tarea_in.get("estado", tarea["estado"])
    prioridad = tarea_in.get("prioridad", tarea["prioridad"])
    
    if descripcion is not None and not descripcion.strip():
        descripcion = tarea["descripcion"]
    
    if estado is not None and estado not in estadosValidos:
        conn.close()
        raise HTTPException(status_code=422, detail="Estado inválido")
    
    if prioridad is not None and prioridad not in prioridadesValidas:
        conn.close()
        raise HTTPException(status_code=422, detail="Prioridad inválida")
    
    cursor.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ? WHERE id = ?",
        (descripcion, estado, prioridad, id)
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
        "fecha_creacion": tarea_actualizada["fecha_creacion"]
    }

@app.delete("/tareas/{id}")
async def BorrarTarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="error: Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}

@app.get("/tareas/resumen")
async def ResumenTareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM tareas")
    total = cursor.fetchone()["count"]
    
    resumen_estado = {estado: 0 for estado in estadosValidos}
    resumen_prioridad = {prioridad: 0 for prioridad in prioridadesValidas}
    
    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado")
    for row in cursor.fetchall():
        if row["estado"] in resumen_estado:
            resumen_estado[row["estado"]] = row["count"]
    
    cursor.execute("SELECT prioridad, COUNT(*) as count FROM tareas GROUP BY prioridad")
    for row in cursor.fetchall():
        if row["prioridad"] in resumen_prioridad:
            resumen_prioridad[row["prioridad"]] = row["count"]
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": resumen_estado,
        "por_prioridad": resumen_prioridad
    }