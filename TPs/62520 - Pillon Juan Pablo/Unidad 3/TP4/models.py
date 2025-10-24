from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat()

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    fecha_creacion: str = Field(default_factory=now_iso)

    @validator("nombre", pre=True)
    def strip_nombre(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if not s:
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return s   

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @validator("nombre", pre=True)
    def strip_nombre_update(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if not s:
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return s

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    fecha_creacion: str = Field(default_factory=now_iso)

    @validator("descripcion", pre=True)
    def strip_descripcion(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if not s:
            raise ValueError("La descripción de la tarea no puede estar vacía")
        return s

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

    @validator("descripcion", pre=True)
    def strip_descripcion_update(cls, v):
        if v is None:
            return v
        s = str(v).strip()
        if not s:
            raise ValueError("La descripción de la tarea no puede estar vacía")
        return s