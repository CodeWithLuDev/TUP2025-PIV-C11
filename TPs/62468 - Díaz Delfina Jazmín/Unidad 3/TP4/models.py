from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ==========================================
# MODELOS PARA PROYECTOS
# ==========================================

class ProyectoCreate(BaseModel):
    """
    Modelo para CREAR un proyecto nuevo
    
    Campos:
    - nombre: Obligatorio, mínimo 1 carácter
    - descripcion: Opcional, puede ser None (vacío)
    """
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del proyecto")
    
    # Ejemplo de uso:
    # { "nombre": "Mi Proyecto", "descripcion": "Un proyecto genial" }


class ProyectoUpdate(BaseModel):
    """
    Modelo para ACTUALIZAR un proyecto existente
    
    Ambos campos son opcionales porque puedes actualizar solo uno de ellos
    """
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None


class ProyectoResponse(BaseModel):
    """
    Modelo para DEVOLVER información de un proyecto
    
    Incluye todos los campos que tiene el proyecto en la base de datos
    """
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    
    class Config:
        # Esto permite que Pydantic trabaje con datos de SQLite
        from_attributes = True


class ProyectoConTareas(ProyectoResponse):
    """
    Modelo extendido que incluye el contador de tareas
    
    Se usa cuando queremos ver un proyecto y saber cuántas tareas tiene
    """
    total_tareas: int = 0


# ==========================================
# MODELOS PARA TAREAS
# ==========================================

class TareaCreate(BaseModel):
    """
    Modelo para CREAR una tarea nueva
    
    Campos:
    - descripcion: Obligatoria
    - estado: Solo puede ser: "pendiente", "en_progreso" o "completada"
    - prioridad: Solo puede ser: "baja", "media" o "alta"
    
    Literal[] hace que Python rechace cualquier otro valor automáticamente
    """
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(
        default="pendiente",
        description="Estado de la tarea"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(
        default="media",
        description="Prioridad de la tarea"
    )
    
    # Ejemplo de uso:
    # {
    #   "descripcion": "Diseñar logo",
    #   "estado": "pendiente",
    #   "prioridad": "alta"
    # }


class TareaUpdate(BaseModel):
    """
    Modelo para ACTUALIZAR una tarea existente
    
    Todos los campos son opcionales, incluyendo cambiar de proyecto
    """
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None  # Permite mover la tarea a otro proyecto


class TareaResponse(BaseModel):
    """
    Modelo para DEVOLVER información de una tarea
    """
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str
    
    class Config:
        from_attributes = True


# ==========================================
# MODELOS PARA ESTADÍSTICAS
# ==========================================

class EstadisticasProyecto(BaseModel):
    """
    Modelo para las estadísticas de un proyecto específico
    
    Ejemplo de respuesta:
    {
      "proyecto_id": 1,
      "proyecto_nombre": "Mi Proyecto",
      "total_tareas": 10,
      "por_estado": {
        "pendiente": 3,
        "en_progreso": 5,
        "completada": 2
      },
      "por_prioridad": {
        "baja": 2,
        "media": 5,
        "alta": 3
      }
    }
    """
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict[str, int]
    por_prioridad: dict[str, int]


class ProyectoTop(BaseModel):
    """
    Información del proyecto con más tareas
    """
    id: int
    nombre: str
    cantidad_tareas: int


class ResumenGeneral(BaseModel):
    """
    Modelo para el resumen general de toda la aplicación
    
    Muestra:
    - Cuántos proyectos hay en total
    - Cuántas tareas hay en total
    - Distribución de tareas por estado
    - Cuál es el proyecto con más tareas
    """
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict[str, int]
    proyecto_con_mas_tareas: Optional[ProyectoTop]