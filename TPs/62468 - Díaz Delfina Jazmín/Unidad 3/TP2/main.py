from fastapi import FastAPI, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum
from itertools import count

app = FastAPI(title="Mini API de Tareas - TP2")

class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

ALLOWED_ESTADOS = {e.value for e in Estado}

# ===== Modelos =====
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Estado = Estado.pendiente

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Estado] = None

class Tarea(TareaBase):
    id: int
    creada_en: datetime

# ===== "BD" en memoria =====
tareas: List[Tarea] = []
_next_id = count(start=1)

# ===== Helpers =====
def error(status: int, msg: str):
    return JSONResponse(status_code=status, content={"error": msg})

def _find_index_by_id(id: int) -> Optional[int]:
    return next((i for i, t in enumerate(tareas) if t.id == id), None)

# ===== Endpoints =====
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[Estado] = Query(None),
    texto: Optional[str] = Query(None)
):
    resultados = tareas

    if estado is not None:
        resultados = [t for t in resultados if t.estado == estado]

    if texto:
        q = texto.lower()
        resultados = [t for t in resultados if q in t.descripcion.lower()]

    # Respetamos tu contrato: envolvemos en {"tareas": [...]}
    return {"tareas": [t.model_dump() for t in resultados]}

@app.post("/tareas")
def crear_tarea(payload: TareaCreate):
    descripcion = payload.descripcion.strip()
    if not descripcion:
        return error(400, "La descripción no puede estar vacía")

    if payload.estado not in ALLOWED_ESTADOS:
        return error(400, "Estado inválido. Valores permitidos: pendiente, en_progreso, completada")

    tarea = Tarea(
        id=next(_next_id),
        descripcion=descripcion,
        estado=payload.estado,  # Estado (Enum o str válido)
        creada_en=datetime.now(timezone.utc)
    )
    tareas.append(tarea)
    return JSONResponse(status_code=201, content=tarea.model_dump())

@app.put("/tareas/{id}")
def actualizar_tarea(id: int = Path(..., ge=1), payload: TareaUpdate = None):
    idx = _find_index_by_id(id)
    if idx is None:
        return error(404, "La tarea no existe")

    if payload is None:
        return error(400, "Payload vacío")

    if payload.descripcion is not None:
        if not payload.descripcion.strip():
            return error(400, "La descripción no puede estar vacía")
        tareas[idx].descripcion = payload.descripcion.strip()

    if payload.estado is not None:
        if payload.estado not in ALLOWED_ESTADOS:
            return error(400, "Estado inválido. Valores permitidos: pendiente, en_progreso, completada")
        tareas[idx].estado = payload.estado  # Enum o str validado

    return tareas[idx].model_dump()

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int = Path(..., ge=1)):
    idx = _find_index_by_id(id)
    if idx is None:
        return error(404, "La tarea no existe")
    tareas.pop(idx)
    return {"mensaje": "Tarea eliminada exitosamente"}

@app.get("/tareas/resumen")
def resumen_tareas() -> Dict[str, int]:
    conteo = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas:
        conteo[t.estado] += 1
    return conteo

@app.put("/tareas/completar_todas")
def completar_todas():
    actualizadas = 0
    for t in tareas:
        if t.estado != Estado.completada:
            t.estado = Estado.completada
            actualizadas += 1
    return {"actualizadas": actualizadas}