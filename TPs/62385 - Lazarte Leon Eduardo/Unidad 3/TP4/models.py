
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Optional
import re

class ProyectoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None

    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v

class ProyectoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None

    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v

class TareaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion: str = Field(..., min_length=1)
    estado: str = Field("pendiente")
    prioridad: str = Field("media")

    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v

    @field_validator('estado')
    @classmethod
    def estado_valido(cls, v: str) -> str:
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado debe ser: pendiente, en_progreso o completada')
        return v

    @field_validator('prioridad')
    @classmethod
    def prioridad_valida(cls, v: str) -> str:
        if v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad debe ser: baja, media o alta')
        return v

class TareaUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    proyecto_id: Optional[int] = None

    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v

    @field_validator('estado')
    @classmethod
    def estado_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado debe ser: pendiente, en_progreso o completada')
        return v

    @field_validator('prioridad')
    @classmethod
    def prioridad_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad debe ser: baja, media o alta')
        return v