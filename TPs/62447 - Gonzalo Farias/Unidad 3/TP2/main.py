from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="Mini API de Tareas - TP2")


tareas_db = []            
ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}  


class TareaBase(BaseModel):
    descripcion: str = Field(..., description="Descripción de la tarea")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(
        default="pendiente", description="Estado actual de la tarea"
    )

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(default=None, description="Nueva descripción")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(
        default=None, description="Nuevo estado"
    )

    @field_validator("descripcion")
    @classmethod
    def validar_desc_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v



def error(status: int, msg: str):
    return JSONResponse(status_code=status, content={"error": msg})

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(
        default=None,
        description='Filtra por estado: "pendiente", "en_progreso" o "completada"'
        ),
    texto: Optional[str] = Query(
        default=None,
        description="Filtra por palabra contenida en la descripción (búsqueda parcial, case-insensitive)"
        ),
):


    if estado is not None and estado not in ALLOWED_ESTADOS:
        return error(400, "Estado inválido")

    
    resultado = tareas_db
    if estado is not None:
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto is not None:
        q = texto.lower()
        resultado = [t for t in resultado if q in t["descripcion"].lower()]
    return resultado

@app.post("/tareas", status_code=201)
def crear_tarea(body: TareaBase):


    nuevo_id = (max((t["id"] for t in tareas_db), default=0) + 1)
    nueva_tarea = {
        "id": nuevo_id,
        "descripcion": body.descripcion.strip(),
        "estado": body.estado or "pendiente",
        "fecha_creacion": datetime.now().isoformat(),
    }
    tareas_db.append(nueva_tarea)
    return nueva_tarea

@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar", "actualizadas": 0}
    
    actualizadas = 0
    for t in tareas_db:
        if t["estado"] != "completada":
            t["estado"] = "completada"
            actualizadas += 1
    return {"mensaje": f"Se completaron {actualizadas} tareas", "actualizadas": actualizadas}

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(
    body: TareaUpdate,
    tarea_id: int = Path(..., ge=1, description="ID de la tarea a modificar")
):
    


    idx = _find_index_by_id(tarea_id)
    if idx is None:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    tarea = tareas_db[idx].copy()

    if body.descripcion is None and body.estado is None:
        return error(400, "No se enviaron campos para actualizar")
    
    tarea = tareas_db[idx].copy()
    if body.descripcion is not None:
        tarea["descripcion"] = body.descripcion.strip()
    if body.estado is not None:
        tarea["estado"] = body.estado
    
    tareas_db[idx] = tarea
    return tarea

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int = Path(..., ge=1, description="ID de la tarea a eliminar")
):
    idx = _find_index_by_id(tarea_id)
    if idx is None:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    eliminada = tareas_db.pop(idx)
    return {"mensaje": "Tarea eliminada", "tarea": eliminada}


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ALLOWED_ESTADOS}
    for t in tareas_db:
        if t["estado"] in resumen:
            resumen[t["estado"]] += 1
    return resumen



def _find_index_by_id(tarea_id: int) -> Optional[int]:
    for i, t in enumerate(tareas_db):
        if t["id"] == tarea_id:
            return i
    return None
