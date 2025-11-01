from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del proyecto")
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v or v.strip() == '':
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=500)
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v or v.strip() == '':
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoResponse(BaseModel):
    """Modelo de respuesta para un proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: int = 0

class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1, max_length=500, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(
        default="pendiente",
        description="Estado de la tarea"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(
        default="media",
        description="Prioridad de la tarea"
    )
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or v.strip() == '':
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or v.strip() == ''):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

class TareaResponse(BaseModel):
    """Modelo de respuesta para una tarea"""
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str

class ResumenProyecto(BaseModel):
    """Modelo para el resumen de un proyecto"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

class ProyectoConMasTareas(BaseModel):
    """Modelo para proyecto con más tareas"""
    id: int
    nombre: str
    cantidad_tareas: int

class ResumenGeneral(BaseModel):
    """Modelo para el resumen general"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[ProyectoConMasTareas]

class Mensaje(BaseModel):
    """Modelo para mensajes de respuesta"""
    mensaje: str
    tareas_eliminadas: Optional[int] = None  # ← AGREGAR ESTO

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    error: str
    detalle: Optional[str] = None