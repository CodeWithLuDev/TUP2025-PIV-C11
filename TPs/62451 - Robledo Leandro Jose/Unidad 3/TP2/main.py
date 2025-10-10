from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# Base de datos en memoria
tareas_db = {}
contador_id = 1

# Modelos Pydantic
class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        estados_validos = ["pendiente", "en_progreso", "completada"]
        if v not in estados_validos:
            raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v is not None:
            estados_validos = ["pendiente", "en_progreso", "completada"]
            if v not in estados_validos:
                raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

# ==================== ENDPOINTS ====================

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None
):
    """
    Obtiene todas las tareas, con filtros opcionales:
    - estado: filtra por estado (pendiente, en_progreso, completada)
    - texto: busca tareas que contengan el texto en la descripción
    """
    tareas = list(tareas_db.values())
    
    # Filtrar por estado si se proporciona
    if estado:
        tareas = [t for t in tareas if t["estado"] == estado]
    
    # Filtrar por texto si se proporciona
    if texto:
        tareas = [t for t in tareas if texto.lower() in t["descripcion"].lower()]
    
    return tareas

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea.
    Validaciones:
    - La descripción no puede estar vacía
    - El estado debe ser válido (pendiente, en_progreso, completada)
    """
    global contador_id
    
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    
    tareas_db[contador_id] = nueva_tarea
    contador_id += 1
    
    return nueva_tarea

@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Devuelve un contador de tareas agrupadas por estado.
    """
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db.values():
        estado = tarea["estado"]
        if estado in resumen:
            resumen[estado] += 1
    
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como completadas.
    """
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db.values():
        tarea["estado"] = "completada"
    
    return {"mensaje": f"Se completaron {len(tareas_db)} tareas"}

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente.
    Se pueden actualizar la descripción y/o el estado.
    """
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    tarea_existente = tareas_db[tarea_id]
    
    # Actualizar solo los campos proporcionados
    if tarea_update.descripcion is not None:
        tarea_existente["descripcion"] = tarea_update.descripcion
    
    if tarea_update.estado is not None:
        tarea_existente["estado"] = tarea_update.estado
    
    return tarea_existente

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """
    Elimina una tarea existente por su ID.
    """
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    del tareas_db[tarea_id]
    
    return {"mensaje": "Tarea eliminada correctamente"}