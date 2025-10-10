from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

app = FastAPI()

# ===== MODELOS =====
class TareaCrear(BaseModel):
    descripcion: str = Field(..., description="Descripción de la tarea")
    estado: str = Field(default="pendiente", description="Estado de la tarea")

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o solo espacios")
        return v.strip()

    @validator("estado")
    def estado_valido(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError(f"Estado inválido. Debe ser uno de: pendiente, en_progreso, completada")
        return v

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía o solo espacios")
        return v.strip() if v is not None else v

    @validator("estado")
    def estado_valido(cls, v):
        if v is not None and v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError(f"Estado inválido. Debe ser uno de: pendiente, en_progreso, completada")
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

# ===== "BASE DE DATOS" EN MEMORIA =====
tareas_db = []
contador_id = 1

# ===== FUNCIONES AUXILIARES =====
def buscar_tarea_por_id(tarea_id: int):
    for tarea in tareas_db:
        if tarea["id"] == tarea_id:
            return tarea
    raise HTTPException(status_code=404, detail="error: La tarea no existe")

# ===== ENDPOINTS =====
@app.get("/")
def inicio():
    return {"mensaje": "API de Tareas - TP2"}

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None)
):
    resultado = tareas_db.copy()
    if estado:
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(status_code=422, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    return resultado

@app.get("/tareas/resumen")
def obtener_resumen():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    return resumen

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCrear):
    global contador_id
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, datos: TareaActualizar):
    tarea = buscar_tarea_por_id(tarea_id)
    if datos.descripcion is not None:
        tarea["descripcion"] = datos.descripcion
    if datos.estado is not None:
        tarea["estado"] = datos.estado
    return tarea

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    tarea = buscar_tarea_por_id(tarea_id)
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada exitosamente", "tarea": tarea}

@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}
