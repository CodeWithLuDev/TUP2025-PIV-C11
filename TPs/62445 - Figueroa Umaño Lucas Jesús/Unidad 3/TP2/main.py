from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import datetime
from typing import Optional

app = FastAPI()

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Enum para estados válidos
class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelo para crear/actualizar tareas
class TareaCreate(BaseModel):
    descripcion: str
    estado: EstadoEnum = EstadoEnum.pendiente
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoEnum] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v

# ==================== ENDPOINTS ====================

@app.get("/tareas")
def obtener_tareas(estado: Optional[EstadoEnum] = None, texto: Optional[str] = None):
    """Obtener todas las tareas con filtros opcionales"""
    resultado = tareas_db.copy()
    
    # Filtrar por estado
    if estado:
        resultado = [t for t in resultado if t["estado"] == estado]
    
    # Filtrar por texto en descripción
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crear una nueva tarea"""
    global contador_id
    
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

@app.get("/tareas/resumen")
def resumen_tareas():
    """Obtener resumen de tareas por estado"""
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas_tareas(body: dict = Body(default={})):
    """Marcar todas las tareas como completadas"""
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    
    return {"mensaje": f"Se completaron {len(tareas_db)} tareas"}

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualizar una tarea existente"""
    for t in tareas_db:
        if t["id"] == id:
            if tarea.descripcion is not None:
                t["descripcion"] = tarea.descripcion
            if tarea.estado is not None:
                t["estado"] = tarea.estado
            return t
    
    raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Eliminar una tarea"""
    for i, t in enumerate(tareas_db):
        if t["id"] == id:
            tareas_db.pop(i)
            return {"mensaje": f"Tarea con id {id} eliminada correctamente"}
    
    raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})