from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

app = FastAPI()

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Modelos
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

# Helpers
def validar_estado(estado: str):
    estados_validos = ["pendiente", "en_progreso", "completada"]
    if estado not in estados_validos:
        raise HTTPException(
            status_code=422,
            detail={"error": "Estado inválido. Solo se permite: pendiente, en_progreso o completada"},
        )

def buscar_tarea(id: int):
    for tarea in tareas_db:
        if tarea["id"] == id:
            return tarea
    return None

# ====================================
# ENDPOINTS - ORDEN CORRECTO
# ====================================

# 1️⃣ RUTAS ESPECÍFICAS PRIMERO (sin parámetros variables)
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas_db:
        resumen[t["estado"]] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron completadas"}

@app.delete("/tareas")
def eliminar_todas():
    tareas_db.clear()
    return {"mensaje": "Todas las tareas eliminadas"}

# 2️⃣ RUTAS GENÉRICAS DESPUÉS
@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    resultado = tareas_db
    if estado:
        validar_estado(estado)
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    return resultado

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCrear):
    global contador_id
    descripcion = tarea.descripcion.strip()
    if not descripcion:
        raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
    validar_estado(tarea.estado)
    nueva = {
        "id": contador_id,
        "descripcion": descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.utcnow().isoformat() + "Z",
    }
    tareas_db.append(nueva)
    contador_id += 1
    return nueva

# 3️⃣ RUTAS CON PARÁMETROS AL FINAL
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, datos: TareaActualizar):
    tarea = buscar_tarea(id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    if datos.descripcion is not None:
        if not datos.descripcion.strip():
            raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
        tarea["descripcion"] = datos.descripcion.strip()
    if datos.estado is not None:
        validar_estado(datos.estado)
        tarea["estado"] = datos.estado
    return tarea

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    tarea = buscar_tarea(id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada"}
