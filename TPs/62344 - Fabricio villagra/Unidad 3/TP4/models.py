from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


# ============== MODELOS DE PROYECTOS ==============

class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def nombre_valido(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre del proyecto no puede estar vacío')
        return v.strip()


class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def nombre_valido(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre del proyecto no puede estar vacío')
        return v.strip() if v else None


class Proyecto(ProyectoCreate):
    """Modelo de proyecto completo"""
    id: int
    fecha_creacion: str


class ProyectoConTareas(Proyecto):
    """Modelo de proyecto con contador de tareas"""
    total_tareas: int = 0


# ============== MODELOS DE TAREAS ==============

class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @validator('descripcion')
    def descripcion_valida(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @validator('descripcion')
    def descripcion_valida(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else None


class Tarea(TareaCreate):
    """Modelo de tarea completo"""
    id: int
    proyecto_id: int
    fecha_creacion: str


class TareaConProyecto(Tarea):
    """Modelo de tarea con información del proyecto"""
    proyecto_nombre: str


# ============== MODELOS DE RESUMEN ==============

class ResumenProyecto(BaseModel):
    """Resumen de estadísticas de un proyecto"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict


class ProyectoMasTareas(BaseModel):
    """Proyecto con más tareas"""
    id: int
    nombre: str
    cantidad_tareas: int


class ResumenGeneral(BaseModel):
    """Resumen general de la aplicación"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[ProyectoMasTareas] = None