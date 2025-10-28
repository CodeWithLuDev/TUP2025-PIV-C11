from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal

# ============== MODELOS PARA PROYECTOS ==============

class ProyectoCreate(BaseModel):
    """Modelo para crear un nuevo proyecto"""
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        """Valida que el nombre no sea solo espacios en blanco"""
        if not v or v.strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto existente"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("El nombre no puede estar vacío")
        return v.strip() if v else v


class ProyectoResponse(BaseModel):
    """Modelo de respuesta para un proyecto"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0


# ============== MODELOS PARA TAREAS ==============

class TareaCreate(BaseModel):
    """Modelo para crear una nueva tarea"""
    descripcion: str = Field(..., min_length=1, max_length=500)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        """Valida que la descripción no sea solo espacios"""
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea existente"""
    descripcion: Optional[str] = Field(None, min_length=1, max_length=500)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v else v


class TareaResponse(BaseModel):
    """Modelo de respuesta para una tarea"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str


# ============== MODELOS DE RESUMEN ==============

class ResumenProyecto(BaseModel):
    """Modelo para el resumen estadístico de un proyecto"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict


class ResumenGeneral(BaseModel):
    """Modelo para el resumen general de la aplicación"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[dict] = None