from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
from fastapi.responses import JSONResponse
import sqlite3
from contextlib import contextmanager

# Enums
class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"

class PrioridadTarea(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

# Modelos Pydantic
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción no puede estar vacía")  
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    prioridad: PrioridadTarea = PrioridadTarea.MEDIA
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)  
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

# Configuración de la base de datos
DB_NAME = "tareas.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.commit()

# Crear la aplicación FastAPI
app = FastAPI(title="Mini API de Tareas", version="1.0.0")

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def startup_event():
    init_db()

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Mini API de Tareas - FastAPI con SQLite"}

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[EstadoTarea] = None,
    texto: Optional[str] = None,
    prioridad: Optional[PrioridadTarea] = None,
    orden: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado.value)
        
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad.value)
        
        # Ordenamiento por fecha de creación
        if orden and orden.lower() in ["asc", "desc"]:
            query += f" ORDER BY fecha_creacion {orden.upper()}"
        else:
            query += " ORDER BY id"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        tareas = []
        for row in rows:
            tareas.append(Tarea(
                id=row["id"],
                descripcion=row["descripcion"],
                estado=row["estado"],
                prioridad=row["prioridad"],
                fecha_creacion=row["fecha_creacion"]
            ))
        
        return tareas

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
            (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, fecha_creacion)
        )
        conn.commit()
        
        tarea_id = cursor.lastrowid
        
        return Tarea(
            id=tarea_id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            fecha_creacion=fecha_creacion
        )

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_existente = cursor.fetchone()
        
        if not tarea_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "La tarea no existe"}
            )
        
        # Preparar datos para actualizar
        descripcion = tarea_update.descripcion if tarea_update.descripcion is not None else tarea_existente["descripcion"]
        estado = tarea_update.estado.value if tarea_update.estado is not None else tarea_existente["estado"]
        prioridad = tarea_update.prioridad.value if tarea_update.prioridad is not None else tarea_existente["prioridad"]
        
        cursor.execute(
            "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ? WHERE id = ?",
            (descripcion, estado, prioridad, id)
        )
        conn.commit()
        
        return Tarea(
            id=id,
            descripcion=descripcion,
            estado=estado,
            prioridad=prioridad,
            fecha_creacion=tarea_existente["fecha_creacion"]
        )

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_existente = cursor.fetchone()
        
        if not tarea_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "La tarea no existe"}
            )
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminada correctamente"}

@app.get("/tareas/resumen")
def obtener_resumen_tareas():
    with get_db() as conn:
        cursor = conn.cursor()
        
        resumen = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        cursor.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
        rows = cursor.fetchall()
        
        for row in rows:
            resumen[row["estado"]] = row["cantidad"]
        
        return resumen

@app.put("/tareas/completar_todas")
def completar_todas_las_tareas():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existan tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "No hay tareas para completar"}
            )
        
        cursor.execute("UPDATE tareas SET estado = ?", (EstadoTarea.COMPLETADA.value,))
        conn.commit()
        
        return {"mensaje": f"Todas las {total} tareas marcadas como completadas"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )