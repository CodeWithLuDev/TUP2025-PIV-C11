from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

app = FastAPI()

estados_permitidos = {"pendiente", "en_progreso", "completada"}

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"

    @validator("descripcion", pre=True)
    def strip_descripcion(cls, v):
        if not isinstance(v, str):
            raise ValueError("Descripción inválida")
        v2 = v.strip()
        if not v2:
            raise ValueError("La descripción no puede estar vacía")
        return v2

    @validator("estado", pre=True, always=True)
    def validar_estado(cls, v):
        v = v or "pendiente"
        if v not in estados_permitidos:
            raise ValueError("Estado inválido")
        return v

class Tarea(TareaCreate):
    id: int
    fecha_creacion: str

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

    @validator("descripcion", pre=True)
    def strip_descripcion_opt(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("Descripción inválida")
        v2 = v.strip()
        if not v2:
            raise ValueError("La descripción no puede estar vacía")
        return v2

    @validator("estado")
    def validar_estado_opt(cls, v):
        if v is None:
            return v
        if v not in estados_permitidos:
            raise ValueError("Estado inválido")
        return v

# DB en memoria como lista de dicts
tareas_db: List[Dict] = []
contador_id = 1

@app.get("/")
def read_root():
    return {"mensaje": "API de Tareas"}

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    global contador_id
    nueva = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado or "pendiente",
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva)
    contador_id += 1
    return nueva

@app.get("/tareas")
def listar_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = list(tareas_db)
    if estado:
        if estado not in estados_permitidos:
            raise HTTPException(status_code=422, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        q = texto.lower()
        resultado = [t for t in resultado if q in t["descripcion"].lower()]
    return resultado

# Rutas fijas: definir antes de la ruta con parámetro {id}
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for tarea in tareas_db:
        estado = tarea.get("estado")
        if estado in resumen:
            resumen[estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# Rutas con parámetro id
@app.put("/tareas/{id}")
def modificar_tarea(id: int, datos: TareaUpdate):
    for tarea in tareas_db:
        if tarea["id"] == id:
            if datos.descripcion is not None:
                tarea["descripcion"] = datos.descripcion
            if datos.estado is not None:
                tarea["estado"] = datos.estado
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea["id"] == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Opcional: evitar 404 por favicon en el navegador
@app.get("/favicon.ico")
def favicon():
    favicon_path = Path(__file__).parent / "favicon.ico"
    if favicon_path.exists():
        return Response(content=favicon_path.read_bytes(), media_type="image/x-icon")
    return Response(status_code=204)