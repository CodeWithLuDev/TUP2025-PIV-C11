"""
TP4: Modelos Pydantic para validación de datos
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ========== MODELOS DE PROYECTOS ==========

class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return str(v).strip()


class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("nombre", mode="before")
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if str(v).strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return str(v).strip()


class Proyecto(BaseModel):
    """Modelo de respuesta de proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0  # Cambiado de cantidad_tareas a total_tareas


# ========== MODELOS DE TAREAS ==========

class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v).strip()


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v).strip()


class Tarea(BaseModel):
    """Modelo de respuesta de tarea"""
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str
    proyecto_nombre: Optional[str] = None