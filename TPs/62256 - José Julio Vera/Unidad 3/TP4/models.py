
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

# ============== MODELOS DE PROYECTOS ==============

class ProyectoBase(BaseModel):
    """Modelo base para proyectos"""
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del proyecto")

class ProyectoCreate(ProyectoBase):
    """Modelo para crear un proyecto"""
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("nombre no puede estar vacío")
        return v.strip()

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("nombre no puede estar vacío")
        return v.strip() if v else None

class ProyectoResponse(ProyectoBase):
    """Modelo de respuesta para un proyecto"""
    id: int
    fecha_creacion: str
    
    class Config:
        from_attributes = True

class ProyectoConTareas(ProyectoResponse):
    """Modelo de respuesta para proyecto con contador de tareas"""
    total_tareas: int

# ============== MODELOS DE TAREAS ==============

class TareaBase(BaseModel):
    """Modelo base para tareas"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(
        "pendiente", 
        description="Estado de la tarea"
    )
    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(
        "media",
        description="Prioridad de la tarea"
    )

class TareaCreate(TareaBase):
    """Modelo para crear una tarea"""
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("descripcion no puede estar vacía")
        return v.strip()

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("descripcion no puede estar vacía")
        return v.strip() if v else None

class TareaResponse(TareaBase):
    """Modelo de respuesta para una tarea"""
    id: int
    proyecto_id: int
    fecha_creacion: str
    
    class Config:
        from_attributes = True

# ============== MODELOS DE RESUMEN Y ESTADÍSTICAS ==============

class ResumenEstado(BaseModel):
    """Modelo para resumen por estado"""
    pendiente: int = 0
    en_progreso: int = 0
    completada: int = 0

class ResumenPrioridad(BaseModel):
    """Modelo para resumen por prioridad"""
    baja: int = 0
    media: int = 0
    alta: int = 0

class ResumenProyecto(BaseModel):
    """Modelo de respuesta para resumen de proyecto"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: ResumenEstado
    por_prioridad: ResumenPrioridad

class ProyectoConMasTareas(BaseModel):
    """Modelo para proyecto con más tareas"""
    id: int
    nombre: str
    cantidad_tareas: int

class ResumenGeneral(BaseModel):
    """Modelo de respuesta para resumen general"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: ResumenEstado
    proyecto_con_mas_tareas: Optional[ProyectoConMasTareas] = None

# ============== MODELOS DE MENSAJES ==============

class MensajeResponse(BaseModel):
    """Modelo para mensajes de respuesta simples"""
    mensaje: str

class MensajeEliminarProyecto(MensajeResponse):
    """Modelo para respuesta de eliminación de proyecto"""
    tareas_eliminadas: int