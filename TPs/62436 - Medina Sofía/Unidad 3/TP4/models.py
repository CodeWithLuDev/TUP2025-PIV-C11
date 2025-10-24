from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def nombre_no_vacio(cls, v):
        if not v or v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = None

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str

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