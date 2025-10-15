# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# -------------------------------
# 1️⃣ Definir modelo de tarea
# -------------------------------
class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1)  # obligatorio y no vacío
    estado: str
    fecha_creacion: datetime

# Estados válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

# Lista en memoria
tareas_db: List[Tarea] = []
id_counter = 1  # Contador para asignar IDs únicos

# -------------------------------
# 2️⃣ Endpoints
# -------------------------------

# --- GET /tareas/resumen --- (ANTES de /tareas/{id})
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

# --- PUT /tareas/completar_todas --- (ANTES de /tareas/{id})
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# --- GET /tareas ---
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultados = tareas_db
    # Filtrar por estado
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail="Estado inválido")
        resultados = [t for t in resultados if t.estado == estado]
    # Filtrar por texto en descripción
    if texto:
        resultados = [t for t in resultados if texto.lower() in t.descripcion.lower()]
    return resultados

# --- POST /tareas ---
class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"  # Estado opcional con valor por defecto
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v and v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v or "pendiente"

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCrear):
    global id_counter
    
    nueva_tarea = Tarea(
        id=id_counter,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    id_counter += 1
    return nueva_tarea

# --- PUT /tareas/{id} ---
class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaActualizar):
    for t in tareas_db:
        if t.id == id:
            if tarea.descripcion is not None:
                t.descripcion = tarea.descripcion
            if tarea.estado is not None:
                t.estado = tarea.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

# --- DELETE /tareas/{id} ---
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas_db:
        if t.id == id:
            tareas_db.remove(t)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})