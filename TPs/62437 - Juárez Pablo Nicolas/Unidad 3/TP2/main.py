from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI()

# Enum para validar los estados válidos
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelo de entrada
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="La descripción no puede estar vacía")
    estado: EstadoTarea = EstadoTarea.pendiente
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip()

# Modelo para actualización (descripcion opcional)
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoTarea] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip() if v else v

# Modelo de salida con ID y fecha
class Tarea(TareaBase):
    id: int
    fecha_creacion: datetime

# Base de datos en memoria
tareas_db: List[Tarea] = []
contador_id = 1

# Crear una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaBase):
    global contador_id

    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

# Contador de tareas por estado (ANTES de las rutas con parámetros)
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

# Marcar todas las tareas como completadas (ANTES de las rutas con parámetros)
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}

    for t in tareas_db:
        t.estado = EstadoTarea.completada
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# Obtener todas las tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[EstadoTarea] = None, texto: Optional[str] = None):
    resultado = tareas_db

    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# Editar una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaUpdate):
    for t in tareas_db:
        if t.id == id:
            if tarea.descripcion is not None:
                t.descripcion = tarea.descripcion
            if tarea.estado is not None:
                t.estado = tarea.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas_db:
        if t.id == id:
            tareas_db.remove(t)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})