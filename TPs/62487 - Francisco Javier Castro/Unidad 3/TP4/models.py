from typing import Optional, Literal
from pydantic import BaseModel, validator

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_strip_if_present(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v.strip() if v is not None else v

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    prioridad: Optional[Literal["baja", "media", "alta"]] = "media"

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("La descripción de la tarea no puede estar vacía")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

    @validator("descripcion")
    def descripcion_strip_if_present(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("La descripción de la tarea no puede estar vacía")
        return v.strip() if v is not None else v
