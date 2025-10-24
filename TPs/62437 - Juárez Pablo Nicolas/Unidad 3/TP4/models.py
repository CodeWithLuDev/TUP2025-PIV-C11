from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

# Modelos para Proyectos
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre del proyecto no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre del proyecto no puede estar vacío')
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0

# Modelos para Tareas
class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción de la tarea no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción de la tarea no puede estar vacía')
        return v.strip() if v else v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str

# Modelos para Estadísticas
class ResumenProyecto(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

class ResumenGeneral(BaseModel):
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[dict] = None