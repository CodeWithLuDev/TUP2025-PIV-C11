from typing import Optional, Literal
from pydantic import BaseModel, validator

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v: str):
        if v is None:
            raise ValueError("El nombre es requerido")
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if v is None:
            return v
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v: str):
        if v is None or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @validator("estado", pre=True, always=True)
    def default_estado(cls, v):
        # Valor por defecto si no se envía
        if v is None:
            return "pendiente"
        return v

    @validator("prioridad", pre=True, always=True)
    def default_prioridad(cls, v):
        if v is None:
            return "media"
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is None:
            return v
        if isinstance(v, str) and v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()