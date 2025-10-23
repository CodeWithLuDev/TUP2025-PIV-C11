from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="Gestión de Tareas")

# =======================
# MODELOS
# =======================
class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1, description="La descripción no puede estar vacía")
    estado: str = Field(..., pattern="^(pendiente|en_progreso|completada)$")
    fecha_creacion: datetime

class CrearTarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field("pendiente", pattern="^(pendiente|en_progreso|completada)$")

class ActualizarTarea(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")

# =======================
# BASE DE DATOS EN MEMORIA
# =======================
tareas: List[Tarea] = []
contador_id = 1

# =======================
# ENDPOINTS
# =======================

@app.get("/tareas", response_model=List[Tarea])
def listar_tareas():
    """Listar todas las tareas"""
    return tareas

@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: CrearTarea):
    """Crear una nueva tarea"""
    global contador_id
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.get("/tareas/{tarea_id}", response_model=Tarea)
def obtener_tarea(tarea_id: int):
    """Obtener una tarea por ID"""
    for tarea in tareas:
        if tarea.id == tarea_id:
            return tarea
    raise HTTPException(status_code=404, detail="Tarea no encontrada")

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int, tarea_actualizada: ActualizarTarea):
    """Actualizar una tarea existente"""
    for tarea in tareas:
        if tarea.id == tarea_id:
            if tarea_actualizada.descripcion is not None:
                tarea.descripcion = tarea_actualizada.descripcion
            if tarea_actualizada.estado is not None:
                tarea.estado = tarea_actualizada.estado
            return tarea
    raise HTTPException(status_code=404, detail="Tarea no encontrada")

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Eliminar una tarea"""
    global tareas
    for tarea in tareas:
        if tarea.id == tarea_id:
            tareas = [t for t in tareas if t.id != tarea_id]
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail="Tarea no encontrada")
