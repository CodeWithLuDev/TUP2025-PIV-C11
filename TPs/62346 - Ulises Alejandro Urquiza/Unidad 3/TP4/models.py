from pydantic import BaseModel, Field
from typing import Optional, Literal

# Modelo para crear un proyecto
class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None

# Modelo para crear una tarea
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]

