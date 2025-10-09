from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
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
    estado: EstadoTarea

# Modelo de salida con ID y fecha
class Tarea(TareaBase):
    id: int
    creada_en: datetime

# Base de datos en memoria
tareas_db: List[Tarea] = []
contador_id = 1

# Crear una nueva tarea
@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaBase):
    global contador_id

    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion.strip(),
        estado=tarea.estado,
        creada_en=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

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
def actualizar_tarea(id: int, tarea: TareaBase):
    for t in tareas_db:
        if t.id == id:
            t.descripcion = tarea.descripcion.strip()
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

# Contador de tareas por estado
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

# Marcar todas las tareas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}

    for t in tareas_db:
        t.estado = EstadoTarea.completada
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"} 