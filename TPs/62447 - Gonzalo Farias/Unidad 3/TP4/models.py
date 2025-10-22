# models.py
from typing import Optional, Literal
from pydantic import BaseModel, field_validator

# --- Constantes permitidas (útiles si querés reutilizar en responses) ---
EstadoLiteral = Literal["pendiente", "en_progreso", "completada"]
PrioridadLiteral = Literal["baja", "media", "alta"]


# -------------------- PROYECTOS --------------------
class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if v is None or v.strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        return v.strip()

    @field_validator("descripcion")
    @classmethod
    def descripcion_trim(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class ProyectoCreate(ProyectoBase):
    """Entrada para POST /proyectos"""
    pass


class ProyectoUpdate(BaseModel):
    """Entrada para PUT /proyectos/{id} — todos opcionales"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def nombre_si_viene_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        return v.strip() if isinstance(v, str) else v

    @field_validator("descripcion")
    @classmethod
    def descripcion_trim(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class ProyectoOut(BaseModel):
    """Salida estándar de un proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str] = None
    fecha_creacion: str


class ProyectoDetalleOut(ProyectoOut):
    """Salida de GET /proyectos/{id} (incluye contador de tareas)"""
    total_tareas: int


# -------------------- TAREAS --------------------
class TareaBase(BaseModel):
    descripcion: str
    estado: EstadoLiteral
    prioridad: PrioridadLiteral

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if v is None or v.strip() == "":
            raise ValueError("La descripción de la tarea no puede estar vacía.")
        return v.strip()


class TareaCreate(TareaBase):
    """Entrada para POST /proyectos/{id}/tareas"""
    pass


class TareaUpdate(BaseModel):
    """Entrada para PUT /tareas/{id} — todos opcionales, puede mover de proyecto"""
    descripcion: Optional[str] = None
    estado: Optional[EstadoLiteral] = None
    prioridad: Optional[PrioridadLiteral] = None
    proyecto_id: Optional[int] = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_si_viene_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            raise ValueError("La descripción de la tarea no puede estar vacía.")
        return v.strip() if isinstance(v, str) else v


class TareaOut(BaseModel):
    id: int
    descripcion: str
    estado: EstadoLiteral
    prioridad: PrioridadLiteral
    proyecto_id: int
    fecha_creacion: str


# -------------------- RESPUESTAS DE RESUMEN --------------------
class ResumenProyectoOut(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict


class ResumenGlobalOut(BaseModel):
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[dict] = None  # {id, nombre, cantidad_tareas} o None si no hay datos
