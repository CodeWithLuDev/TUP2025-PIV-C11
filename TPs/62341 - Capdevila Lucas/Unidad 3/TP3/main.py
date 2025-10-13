"""
TP3.2: Mini API de Tareas con FastAPI

Este archivo implementa una API REST en memoria para gestionar tareas, 
incluyendo CRUD, filtros por query params, validaciones y rutas extra.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str
    prioridad: str


ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# Database configuration
DB_NAME = "tareas.db"


def init_db():
    """Initialize the database and create tables if they don't exist"""
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_creacion TEXT,
                prioridad TEXT NOT NULL
            )
        """)
        conn.commit()


def dict_from_row(cursor, row):
    """Convert SQLite row to dictionary"""
    return {description[0]: row[i] for i, description in enumerate(cursor.description)}


class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = None
    prioridad: Optional[str] = "media"

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v)

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "media"
        if v not in PRIORIDADES_VALIDAS:
            raise ValueError("Prioridad inválida")
        return v


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v)

    @field_validator("estado")
    @classmethod
    def validar_estado_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in PRIORIDADES_VALIDAS:
            raise ValueError("Prioridad inválida")
        return v


app = FastAPI(
    title="Mini API de Tareas",
    description="CRUD persistente con SQLite y FastAPI",
    version="1.0.0",
)

# Initialize database on startup
init_db()


@app.get("/")
async def raiz():
    return {
        "nombre": "Mini API de Tareas",
        "version": "1.0.0",
        "descripcion": "API REST para gestión de tareas con persistencia en SQLite",
        "endpoints": {
            "GET /": "Información de la API",
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/{id}": "Actualizar tarea existente",
            "DELETE /tareas/{id}": "Eliminar tarea",
            "GET /tareas/resumen": "Resumen estadístico de tareas",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }


@app.get("/tareas")
async def obtener_tareas(
    estado: Optional[str] = Query(default=None),
    texto: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default=None),
):
    if estado is not None and estado not in ESTADOS_VALIDOS:
        # 400 Bad Request si el estado del filtro es inválido
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    
    if prioridad is not None and prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})

    # Build dynamic SQL query
    query = "SELECT * FROM tareas"
    conditions = []
    params = []
    
    if estado is not None:
        conditions.append("estado = ?")
        params.append(estado)
    
    if texto is not None:
        conditions.append("descripcion LIKE ?")
        params.append(f"%{texto}%")
    
    if prioridad is not None:
        conditions.append("prioridad = ?")
        params.append(prioridad)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Add ordering
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    else:
        query += " ORDER BY fecha_creacion ASC"  # Default ordering
    
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict_from_row(cursor, row) for row in rows]


@app.post("/tareas", status_code=201)
async def crear_tarea(payload: TareaCreate):
    estado = payload.estado if payload.estado is not None else "pendiente"
    prioridad = payload.prioridad if payload.prioridad is not None else "media"
    
    # Validación final de estado y prioridad
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    if prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})

    fecha_creacion = datetime.now(timezone.utc).isoformat()
    
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
            (payload.descripcion.strip(), estado, fecha_creacion, prioridad)
        )
        tarea_id = cursor.lastrowid
        conn.commit()
        
        # Get the created task
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        return dict_from_row(cursor, row)


@app.put("/tareas/completar_todas")
async def completar_todas():
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tareas")
        count = cursor.fetchone()[0]
        
        if count == 0:
            return {"mensaje": "No hay tareas para completar"}
        
        cursor.execute("UPDATE tareas SET estado = 'completada'")
        conn.commit()
        return {"mensaje": "Todas las tareas fueron marcadas como completadas"}


@app.put("/tareas/{tarea_id}")
async def actualizar_tarea(tarea_id: int, payload: TareaUpdate):
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        # Build dynamic UPDATE query
        updates = []
        params = []
        
        if payload.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(payload.descripcion.strip())
        
        if payload.estado is not None:
            if payload.estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
            updates.append("estado = ?")
            params.append(payload.estado)
        
        if payload.prioridad is not None:
            if payload.prioridad not in PRIORIDADES_VALIDAS:
                raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})
            updates.append("prioridad = ?")
            params.append(payload.prioridad)
        
        if updates:
            query = "UPDATE tareas SET " + ", ".join(updates) + " WHERE id = ?"
            params.append(tarea_id)
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated task
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        return dict_from_row(cursor, row)


@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea(tarea_id: int):
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        conn.commit()
        return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
async def resumen_tareas():
    with sqlite3.connect(DB_NAME, timeout=30.0) as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM tareas")
        total_tareas = cursor.fetchone()[0]
        
        # Get counts by estado
        cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
        por_estado = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get counts by prioridad
        cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
        por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }


# Nota: no se define un handler global 404 para preservar el formato estándar
# {"detail": ...} esperado por los tests cuando se lanza HTTPException(404).


if __name__ == "__main__":
    import uvicorn

    print("=== MINI API DE TAREAS ===")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)


