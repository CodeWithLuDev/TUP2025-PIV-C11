from fastapi import APIRouter, Body, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# Estados válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

# Modelo completo de Tarea
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

# Modelo para crear tareas
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(default="pendiente")

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @field_validator("estado")
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

# Modelo para actualizar tareas (parcial)
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v is not None else v

    @field_validator("estado")
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

# Base de datos en memoria
tareas_db: List[Tarea] = []
ultimo_id = 0

# Función auxiliar
def obtener_tarea_por_id(tarea_id: int) -> Optional[Tarea]:
    return next((t for t in tareas_db if t.id == tarea_id), None)

# CRUD de tareas

@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    global ultimo_id
    ultimo_id += 1
    nueva_tarea = Tarea(
        id=ultimo_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    return nueva_tarea

@app.put("/tareas/completar_todas", response_model=dict)
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": f"Se completaron {len(tareas_db)} tareas"}

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int, datos: TareaUpdate):
    tarea = obtener_tarea_por_id(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    if datos.descripcion is not None:
        tarea.descripcion = datos.descripcion
    if datos.estado is not None:
        tarea.estado = datos.estado
    return tarea

@app.delete("/tareas/{tarea_id}", response_model=dict)
def eliminar_tarea(tarea_id: int):
    tarea = obtener_tarea_por_id(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada correctamente"}

@app.get("/tareas/resumen", response_model=dict)
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen