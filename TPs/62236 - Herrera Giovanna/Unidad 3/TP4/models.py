from pydantic import BaseModel
from typing import Optional, Literal

# Modelos para Proyectos
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoUpdate(BaseModel):
    nombre: Optional[str]
    descripcion: Optional[str]

# Modelos para Tareas
class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]

class TareaUpdate(BaseModel):
    descripcion: Optional[str]
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]]
    prioridad: Optional[Literal["baja", "media", "alta"]]
    proyecto_id: Optional[int]