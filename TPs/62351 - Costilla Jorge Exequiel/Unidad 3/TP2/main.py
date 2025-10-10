from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

app = FastAPI()

# MODELOS

class EstadoEnum(str, Enum):
    """Enum con los estados válidos de una tarea"""
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"


class TareaBase(BaseModel):
    """Modelo base para tareas (sin ID ni fecha)"""
    descripcion: str
    estado: EstadoEnum = EstadoEnum.pendiente

    @field_validator("descripcion", mode="before")
    def validar_descripcion(cls, v):
        """Validar que la descripción no esté vacía o solo con espacios"""
        if isinstance(v, str) and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v


class Tarea(TareaBase):
    """Modelo completo de una tarea con ID y fecha"""
    id: int
    fecha_creacion: str


#  BASE DE DATOS EN MEMORIA 

tareas_db: dict = {}  # {id: tarea_dict}
contador_id = 1


# RUTAS GET 

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[EstadoEnum] = Query(None),
    texto: Optional[str] = Query(None)
):
    """
    Obtener todas las tareas, con filtros opcionales:
    - ?estado=pendiente (filtra por estado)
    - ?texto=palabra (busca en la descripción)
    """
    tareas = list(tareas_db.values())
    
    # Filtrar por estado si se proporciona
    if estado:
        tareas = [t for t in tareas if t["estado"] == estado]
    
    # Filtrar por texto si se proporciona (búsqueda insensible a mayúsculas)
    if texto:
        tareas = [
            t for t in tareas 
            if texto.lower() in t["descripcion"].lower()
        ]
    
    return tareas


@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Obtener resumen con contador de tareas por estado.
    Nota: Esta ruta debe ir ANTES de /tareas/{id} en la definición
    para que FastAPI la reconozca correctamente.
    """
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db.values():
        resumen[tarea["estado"]] += 1
    
    return resumen


# RUTAS POST 

@app.post("/tareas", status_code=201, response_model=Tarea)
def crear_tarea(tarea: TareaBase):
    """
    Crear una nueva tarea.
    - Validación automática de descripción (no vacía)
    - Estado por defecto: "pendiente"
    - Asigna fecha_creacion automáticamente
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


#  RUTAS PUT 

class TareaActualizacion(BaseModel):
    """Modelo para actualización de tareas (campos opcionales)"""
    descripcion: Optional[str] = None
    estado: Optional[EstadoEnum] = None

    @field_validator("descripcion", mode="before")
    def validar_descripcion_actualizacion(cls, v):
        """Validar descripción solo si se proporciona"""
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v


@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marcar todas las tareas como completadas.
    Retorna un mensaje indicando cuántas se completaron.
    NOTA: Esta ruta debe ir ANTES de /tareas/{tarea_id}
    """
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    cantidad = 0
    for tarea in tareas_db.values():
        tarea["estado"] = "completada"
        cantidad += 1
    
    return {"mensaje": f"Se marcaron {cantidad} tarea(s) como completada(s)"}


@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int, tarea_actualizada: TareaActualizacion):
    """
    Actualizar una tarea existente.
    - Retorna 404 si la tarea no existe
    - Permite actualizar descripción y estado de forma parcial
    """
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=404,
            detail={"error": f"La tarea con ID {tarea_id} no existe"}
        )
    
    tarea_existente = tareas_db[tarea_id]
    
    # Solo actualizar los campos que se proporcionen
    if tarea_actualizada.descripcion is not None:
        tarea_existente["descripcion"] = tarea_actualizada.descripcion
    if tarea_actualizada.estado is not None:
        tarea_existente["estado"] = tarea_actualizada.estado
    
    return tarea_existente


#  RUTAS DELETE 

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """
    Eliminar una tarea existente.
    - Retorna 404 si la tarea no existe
    - Retorna un mensaje de confirmación
    """
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=404,
            detail={"error": f"La tarea con ID {tarea_id} no existe"}
        )
    
    del tareas_db[tarea_id]
    
    return {"mensaje": f"Tarea con ID {tarea_id} eliminada correctamente"}