"""
TP3.2: Mini API de Tareas con FastAPI

Este archivo implementa una API REST en memoria para gestionar tareas, 
incluyendo CRUD, filtros por query params, validaciones y rutas extra.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str


ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}


class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v)

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def validar_descripcion_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if str(v).strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return str(v)

    @field_validator("estado")
    @classmethod
    def validar_estado_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v


app = FastAPI(
    title="Mini API de Tareas",
    description="CRUD básico en memoria con FastAPI",
    version="1.0.0",
)


tareas_db: List[Dict] = []
contador_id: int = 1


@app.get("/")
async def raiz():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}


@app.get("/tareas")
async def obtener_tareas(
    estado: Optional[str] = Query(default=None),
    texto: Optional[str] = Query(default=None),
):
    if estado is not None and estado not in ESTADOS_VALIDOS:
        # 400 Bad Request si el estado del filtro es inválido
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    resultados = tareas_db
    if estado is not None:
        resultados = [t for t in resultados if t["estado"] == estado]
    if texto is not None:
        query = texto.lower()
        resultados = [t for t in resultados if query in t["descripcion"].lower()]
    return resultados


@app.post("/tareas", status_code=201)
async def crear_tarea(payload: TareaCreate):
    global contador_id

    estado = payload.estado if payload.estado is not None else "pendiente"
    # Validación final de estado (por si llega None u otro valor)
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    nueva_tarea = {
        "id": contador_id,
        "descripcion": payload.descripcion.strip(),
        "estado": estado,
        "fecha_creacion": datetime.utcnow().isoformat(),
    }
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea


def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict]:
    for tarea in tareas_db:
        if tarea["id"] == tarea_id:
            return tarea
    return None


@app.put("/tareas/completar_todas")
async def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}


@app.put("/tareas/{tarea_id}")
async def actualizar_tarea(tarea_id: int, payload: TareaUpdate):
    tarea = obtener_tarea_por_id(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    if payload.descripcion is not None:
        tarea["descripcion"] = payload.descripcion.strip()
    if payload.estado is not None:
        if payload.estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        tarea["estado"] = payload.estado
    return tarea


@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea(tarea_id: int):
    tarea = obtener_tarea_por_id(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
async def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for tarea in tareas_db:
        estado = tarea["estado"]
        if estado in resumen:
            resumen[estado] += 1
    return resumen


# Nota: no se define un handler global 404 para preservar el formato estándar
# {"detail": ...} esperado por los tests cuando se lanza HTTPException(404).


if __name__ == "__main__":
    import uvicorn

    print("=== MINI API DE TAREAS ===")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)


