from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

#  MODELOS DE PROYECTOS 

class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción del proyecto")
    
    @field_validator('nombre')
    def nombre_no_vacio(cls, v):
        if not v or v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    """Modelo de respuesta para un proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0

#  MODELOS DE TAREAS 

class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(
        default="pendiente",
        description="Estado de la tarea"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(
        default="media",
        description="Prioridad de la tarea"
    )
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto al que pertenece")
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
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