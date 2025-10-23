from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

# ============ MODELOS DE PROYECTO ============

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v.strip() == "":
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip() if v else None

class Proyecto(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0

# ============ MODELOS DE TAREA ============

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip() if v else None

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    proyecto_nombre: Optional[str] = None
    fecha_creacion: str

# ============ MODELOS DE RESPUESTA ============

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