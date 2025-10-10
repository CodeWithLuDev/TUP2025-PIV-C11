from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime, timezone

# ---------- Config / Constantes ----------
class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

VALID_ESTADOS = {e.value for e in Estado}

# Variables globales para tests
contador_id = 1
tareas_db = {}

# ---------- Modelos ----------
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Estado = Field(Estado.pendiente, description="Estado de la tarea")

    @validator("descripcion")
    def descripcion_no_vacia(cls, v: str):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

class TareaCrear(TareaBase):
    """Modelo para crear tarea. 'estado' es opcional y por defecto 'pendiente'."""
    pass

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = Field(None, description="Nueva descripción")
    estado: Optional[Estado] = Field(None, description="Nuevo estado")

    @validator("descripcion")
    def descripcion_si_presente_no_vacia(cls, v: Optional[str]):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if isinstance(v, str) else v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str  # ISO timestamp

# ---------- App ----------
app = FastAPI(title="Mini API de Tareas - TP2", version="1.0.0")

# ---------- Helpers ----------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------- Endpoints ----------

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[str] = Query(None, description="Filtrar por estado"),
                   texto: Optional[str] = Query(None, description="Buscar texto en descripcion")):
    """
    Obtener todas las tareas. Opcionalmente filtrar por estado y/o buscar por texto en la descripción.
    """
    resultados = list(tareas_db.values())

    if estado is not None:
        if estado not in VALID_ESTADOS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"error": f"Estado inválido. Valores válidos: {sorted(VALID_ESTADOS)}"})
        resultados = [t for t in resultados if t.estado == estado]

    if texto is not None:
        q = texto.strip().lower()
        resultados = [t for t in resultados if q in t.descripcion.lower()]

    return resultados

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(payload: TareaCrear):
    """
    Crear una nueva tarea. La descripción no puede estar vacía.
    """
    global contador_id
    
    tarea_id = contador_id
    contador_id += 1
    
    tarea = Tarea(
        id=tarea_id,
        descripcion=payload.descripcion,
        estado=payload.estado,
        fecha_creacion=_now_iso()
    )
    tareas_db[tarea_id] = tarea
    return tarea

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int = Path(..., ge=1), payload: TareaActualizar = ...):
    """
    Actualizar una tarea por id. Si no existe -> 404.
    Validaciones:
      - Si se proporciona 'estado', debe ser uno de los permitidos.
      - Si se proporciona 'descripcion', no puede estar vacía.
    """
    if tarea_id not in tareas_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "La tarea no existe"})

    tarea = tareas_db[tarea_id]

    # Validación estado (Pydantic ya lo hace al parsear a Enum), pero chequeo extra por seguridad:
    if payload.estado is not None and payload.estado not in Estado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"error": f"Estado inválido. Valores válidos: {sorted(VALID_ESTADOS)}"})

    # Aplicar cambios (solo los que vienen)
    if payload.descripcion is not None:
        tarea.descripcion = payload.descripcion
    if payload.estado is not None:
        tarea.estado = payload.estado

    tareas_db[tarea_id] = tarea
    return tarea

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int = Path(..., ge=1)):
    """
    Eliminar una tarea por id. Si no existe -> 404.
    Retorna JSON con mensaje claro.
    """
    if tarea_id not in tareas_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "La tarea no existe"})
    
    del tareas_db[tarea_id]
    return {"mensaje": "Tarea eliminada correctamente"}

@app.get("/tareas/resumen")
def resumen_tareas():
    """
    Devuelve el contador de tareas por estado.
    """
    resumen = {e.value: 0 for e in Estado}
    for t in tareas_db.values():
        resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como 'completada'.
    Retorna mensaje con cantidad de tareas actualizadas.
    """
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}

    actualizadas = 0
    for tarea_id, tarea in tareas_db.items():
        if tarea.estado != Estado.completada:
            tarea.estado = Estado.completada
            tareas_db[tarea_id] = tarea
            actualizadas += 1

    return {"mensaje": f"Se completaron {actualizadas} tareas"}

# ---------- Manejo global de errores ----------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    Normaliza la respuesta para que contenga siempre JSON con 'error' o el detail si viene así.
    """
    detail = exc.detail
    if isinstance(detail, dict):
        body = detail
    elif isinstance(detail, str):
        body = {"error": detail}
    else:
        body = {"error": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=body)