from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field  
from typing import List, Optional
from datetime import datetime
from enum import Enum
from fastapi.responses import JSONResponse

class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción no puede estar vacía")  
    estado: EstadoTarea = EstadoTarea.PENDIENTE

class Tarea(TareaCreate):
    id: int
    fecha_creacion: datetime

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)  
    estado: Optional[EstadoTarea] = None

app = FastAPI(title="Mini API de Tareas", version="1.0.0")

tareas_db = []
contador_id = 1

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[EstadoTarea] = None,
    texto: Optional[str] = None
):
    tareas_filtradas = tareas_db
    
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t.estado == estado]
    
    if texto:
        tareas_filtradas = [t for t in tareas_filtradas if texto.lower() in t.descripcion.lower()]
    
    return tareas_filtradas

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCreate):
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

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
 
    tarea_encontrada = None
    for tarea in tareas_db:
        if tarea.id == id:
            tarea_encontrada = tarea
            break
    
    if not tarea_encontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "La tarea no existe"}
        )
    
    if tarea_update.descripcion is not None:
        tarea_encontrada.descripcion = tarea_update.descripcion
    
    if tarea_update.estado is not None:
        tarea_encontrada.estado = tarea_update.estado
    
    return tarea_encontrada

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    global tareas_db
    
    tarea_encontrada = None
    for tarea in tareas_db:
        if tarea.id == id:
            tarea_encontrada = tarea
            break
    
    if not tarea_encontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "La tarea no existe"}
        )
    
    tareas_db = [tarea for tarea in tareas_db if tarea.id != id]
    return {"mensaje": "Tarea eliminada correctamente"}

@app.get("/tareas/resumen")
def obtener_resumen_tareas():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea.estado] += 1
    
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas_las_tareas():
    for tarea in tareas_db:
        tarea.estado = EstadoTarea.COMPLETADA
    
    return {"mensaje": f"Todas las {len(tareas_db)} tareas marcadas como completadas"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.get("/")
def read_root():
    return {"message": "Mini API de Tareas - FastAPI"}