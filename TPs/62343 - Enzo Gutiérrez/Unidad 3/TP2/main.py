from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Modelos Pydantic
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    fecha_creacion: str


# Rutas

@app.get("/")
def read_root():
    return {"message": "Mini API de Tareas - TP2"}


@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None)
):
    """
    Obtiene todas las tareas, con filtros opcionales por estado o texto en descripción.
    """
    resultado = tareas_db.copy()
    
    # Filtrar por estado
    if estado:
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(status_code=400, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]
    
    # Filtrar por texto en descripción
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea.
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
def resumen_tareas():
    """
    Devuelve un contador de tareas por estado.
    """
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como completadas.
    """
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas para completar"}
    
    tareas_actualizadas = 0
    
    for tarea in tareas_db:
        if tarea["estado"] != "completada":
            tarea["estado"] = "completada"
            tareas_actualizadas += 1
    
    return {
        "mensaje": "Todas las tareas han sido completadas",
        "tareas_actualizadas": tareas_actualizadas
    }


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """
    Actualiza una tarea existente por ID.
    """
    # Buscar la tarea
    tarea_existente = None
    indice = -1
    
    for i, t in enumerate(tareas_db):
        if t["id"] == id:
            tarea_existente = t
            indice = i
            break
    
    if not tarea_existente:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Actualizar descripción si se proporciona
    if tarea.descripcion is not None:
        tarea_existente["descripcion"] = tarea.descripcion
    
    # Actualizar estado si se proporciona
    if tarea.estado is not None:
        tarea_existente["estado"] = tarea.estado
    
    tareas_db[indice] = tarea_existente
    
    return tarea_existente


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea por ID.
    """
    global tareas_db
    
    # Buscar la tarea
    tarea_existente = None
    indice = -1
    
    for i, t in enumerate(tareas_db):
        if t["id"] == id:
            tarea_existente = t
            indice = i
            break
    
    if not tarea_existente:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    tareas_db.pop(indice)
    
    return {"mensaje": "Tarea eliminada exitosamente"}


# Endpoint adicional para resetear la base de datos (útil para testing)
@app.delete("/tareas")
def eliminar_todas_tareas():
    """
    Elimina todas las tareas (útil para testing).
    """
    global tareas_db, contador_id
    tareas_db = []
    contador_id = 1
    return {"mensaje": "Todas las tareas han sido eliminadas"}