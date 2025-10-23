from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI()

# Modelo de datos para las tareas
class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Ruta raíz
@app.get("/")
def root():
    return {"mensaje": "API de Tareas"}

# 1. GET /tareas - Obtener todas las tareas (con filtros opcionales)
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None)
):
    resultado = tareas_db.copy()
    
    # Filtrar por estado
    if estado:
        resultado = [t for t in resultado if t["estado"] == estado]
    
    # Filtrar por texto en descripción
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

# 2. GET /tareas/resumen - Contador de tareas por estado
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    
    return resumen

# 3. POST /tareas - Crear una nueva tarea
@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
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

# 4. PUT /tareas/completar_todas - Marcar todas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

# 5. PUT /tareas/{id} - Actualizar una tarea existente
@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    # Buscar la tarea
    tarea_encontrada = None
    for tarea in tareas_db:
        if tarea["id"] == id:
            tarea_encontrada = tarea
            break
    
    if not tarea_encontrada:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Actualizar campos
    if tarea_update.descripcion is not None:
        tarea_encontrada["descripcion"] = tarea_update.descripcion
    
    if tarea_update.estado is not None:
        tarea_encontrada["estado"] = tarea_update.estado
    
    return tarea_encontrada

# 6. DELETE /tareas/{id} - Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    global tareas_db
    
    # Buscar índice de la tarea
    indice = None
    for i, tarea in enumerate(tareas_db):
        if tarea["id"] == id:
            indice = i
            break
    
    if indice is None:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    tarea_eliminada = tareas_db.pop(indice)
    return {"mensaje": "Tarea eliminada exitosamente", "tarea": tarea_eliminada}