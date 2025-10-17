from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Enumeración para los estados válidos
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelos Pydantic para validación de datos
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: EstadoTarea = Field(default=EstadoTarea.pendiente, description="Estado de la tarea")
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoTarea] = None
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    fecha_creacion: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Inicializar FastAPI
app = FastAPI(
    title="API de Tareas",
    description="Mini API CRUD para gestión de tareas",
    version="1.0.0"
)

# Almacenamiento en memoria
tareas_db: List[dict] = []
contador_id: int = 1

# Función auxiliar para encontrar tarea por ID
def buscar_tarea(tarea_id: int) -> Optional[dict]:
    for tarea in tareas_db:
        if tarea["id"] == tarea_id:
            return tarea
    return None

# RUTAS DE LA API

@app.get("/")
def root():
    """
    Endpoint de bienvenida
    """
    return {
        "mensaje": "API de Tareas - TP2",
        "version": "1.0.0",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Devuelve un contador de tareas por cada estado.
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
def completar_todas_tareas():
    """
    Marca todas las tareas como completadas.
    """
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    
    tareas_actualizadas = 0
    
    for tarea in tareas_db:
        if tarea["estado"] != EstadoTarea.completada:
            tarea["estado"] = EstadoTarea.completada
            tareas_actualizadas += 1
    
    return {
        "mensaje": "Todas las tareas han sido marcadas como completadas",
        "tareas_actualizadas": tareas_actualizadas
    }

@app.get("/tareas", response_model=List[TareaResponse])
def listar_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Buscar texto en descripción")
):
    """
    Lista todas las tareas con filtros opcionales.
    - estado: filtra por estado específico
    - texto: busca coincidencias en la descripción
    """
    tareas_filtradas = tareas_db.copy()
    
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t["estado"] == estado]
    
    if texto:
        tareas_filtradas = [
            t for t in tareas_filtradas 
            if texto.lower() in t["descripcion"].lower()
        ]
    
    return tareas_filtradas

@app.post("/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea.
    - Valida que la descripción no esté vacía
    - Asigna ID automático y fecha de creación
    """
    global contador_id
    
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now()
    }
    
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

@app.put("/tareas/{id}", response_model=TareaResponse)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente.
    - Permite modificar descripción y/o estado
    - Devuelve 404 si la tarea no existe
    """
    tarea = buscar_tarea(id)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    # Actualizar solo los campos proporcionados
    if tarea_update.descripcion is not None:
        tarea["descripcion"] = tarea_update.descripcion
    
    if tarea_update.estado is not None:
        tarea["estado"] = tarea_update.estado
    
    return tarea

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea por su ID.
    - Devuelve 404 si la tarea no existe
    """
    tarea = buscar_tarea(id)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    tareas_db.remove(tarea)
    
    return {"mensaje": "Tarea eliminada exitosamente"}