# models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

ESTADOS = ("pendiente", "en_progreso", "completada")
PRIORIDADES = ("baja", "media", "alta")

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_valido(cls, v):
        if v is not None and not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip() if v is not None else v

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    proyecto_id: Optional[int] = None

    @validator("descripcion")
    def descripcion_strip(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v is not None else v
