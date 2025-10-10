from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="Mini API de Tareas", version="1.0.0")

tareas_db = []
contador_id = 1

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str


@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None)
):
    """
    Obtiene todas las tareas con filtros opcionales.
    - estado: filtra por estado (pendiente, en_progreso, completada)
    - texto: busca tareas que contengan el texto en la descripción
    """
    resultado = tareas_db.copy()
    
    if estado:
        resultado = [t for t in resultado if t["estado"] == estado]
    
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea.
    - descripcion: texto descriptivo de la tarea (no puede estar vacío)
    - estado: estado de la tarea (pendiente por defecto)
    """
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
def obtener_resumen():
    """
    Obtiene un resumen con el contador de tareas por estado.
    """
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        estado = tarea["estado"]
        if estado in resumen:
            resumen[estado] += 1
    
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como completadas.
    """
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    
    return {"mensaje": f"{len(tareas_db)} tareas marcadas como completadas"}

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """
    Actualiza una tarea existente por su ID.
    - descripcion: nueva descripción (opcional)
    - estado: nuevo estado (opcional)
    """
    tarea_encontrada = None
    for t in tareas_db:
        if t["id"] == id:
            tarea_encontrada = t
            break
    
    if not tarea_encontrada:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    if tarea.descripcion is not None:
        tarea_encontrada["descripcion"] = tarea.descripcion
    
    if tarea.estado is not None:
        tarea_encontrada["estado"] = tarea.estado
    
    return tarea_encontrada

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea por su ID.
    """
    global tareas_db
    
    indice = None
    for i, t in enumerate(tareas_db):
        if t["id"] == id:
            indice = i
            break
    
    if indice is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    tareas_db.pop(indice)
    
    return {"mensaje": f"Tarea {id} eliminada exitosamente"}