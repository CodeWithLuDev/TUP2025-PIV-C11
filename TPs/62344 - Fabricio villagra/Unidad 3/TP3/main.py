import sqlite3
import os
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

# Configuración
DB_NAME = "tareas.db"
app = FastAPI(title="API de Tareas Persistente")

# ============== MODELOS PYDANTIC ==============

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = "pendiente"
    prioridad: Optional[str] = "media"
    
    @validator('descripcion')
    def descripcion_no_espacios(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()
    
    @validator('estado')
    def estado_valido(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado debe ser: pendiente, en_progreso o completada')
        return v
    
    @validator('prioridad')
    def prioridad_valida(cls, v):
        if v and v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad debe ser: baja, media o alta')
        return v


class Tarea(TareaCreate):
    id: int
    fecha_creacion: str


class ResumenTareas(BaseModel):
    total_tareas: int
    por_estado: dict
    por_prioridad: dict


# ============== FUNCIONES DE BASE DE DATOS ==============

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT,
            prioridad TEXT DEFAULT 'media'
        )
    ''')
    
    conn.commit()
    conn.close()


def get_connection():
    """Devuelve una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============== EVENTOS DE LA APLICACIÓN ==============

@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar la aplicación"""
    init_db()


# ============== ENDPOINTS ==============

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API de Tareas Persistente",
        "version": "1.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas como completadas"
        }
    }


@app.get("/tareas", response_model=List[Tarea])
async def get_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = "asc"
):
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
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


@app.post("/tareas", response_model=Tarea, status_code=201)
async def create_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    ''', (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    # Retornar la tarea creada
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha_creacion,
        "prioridad": tarea.prioridad
    }


@app.put("/tareas/{tarea_id}", response_model=Tarea)
async def update_tarea(tarea_id: int, tarea_update: TareaCreate):
    """Actualiza una tarea existente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    cursor.execute('''
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    ''', (tarea_update.descripcion, tarea_update.estado, tarea_update.prioridad, tarea_id))
    
    conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)


@app.delete("/tareas/{tarea_id}")
async def delete_tarea(tarea_id: int):
    """Elimina una tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}


@app.get("/tareas/resumen", response_model=ResumenTareas)
async def get_resumen():
    """Devuelve un resumen de las tareas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    
    # Por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    # Por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
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
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


@app.put("/tareas/completar_todas")
async def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}


# ============== PUNTO DE ENTRADA ==============

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)