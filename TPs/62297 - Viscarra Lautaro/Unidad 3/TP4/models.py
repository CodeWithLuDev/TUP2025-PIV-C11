from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Literal



class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str
    descripcion: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, valor):
        if not valor or valor.strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        return valor.strip()


class ProyectoResponse(ProyectoCreate):
    """Modelo de respuesta de proyecto"""
    id: int
    fecha_creacion: str


class ProyectoConTareas(ProyectoResponse):
    """Modelo de proyecto con contador de tareas"""
    total_tareas: int



class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, valor):
        if not valor or valor.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return valor.strip()


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, valor):
        if valor is not None and (not valor or valor.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return valor.strip() if valor else valor


class TareaResponse(TareaCreate):
    """Modelo de respuesta de tarea"""
    id: int
    proyecto_id: int
    fecha_creacion: str