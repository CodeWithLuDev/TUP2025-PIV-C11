# server.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# 🧩 Modelo de datos
estados_permitidos = {"pendiente", "en_progreso", "completada"}

class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1)
    estado: str
    fecha_creacion: datetime

# 🧠 Base de datos en memoria
tareas_db: List[Tarea] = []

@app.get("/") 
def read_root():
    return {"message": "API de Gestión de Tareas"}


# 📥 POST /tareas
@app.post("/tareas")
def crear_tarea(tarea: Tarea):
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
    if tarea.estado not in estados_permitidos:
        raise HTTPException(status_code=400, detail="Estado inválido")
    tareas_db.append(tarea)
    return tarea

# 📤 GET /tareas
@app.get("/tareas")
def listar_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# 🔄 PUT /tareas/{id}
@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea_actualizada: Tarea):
    if tarea_actualizada.estado not in estados_permitidos:
        raise HTTPException(status_code=400, detail="Estado inválido")
    for i, tarea in enumerate(tareas_db):
        if tarea.id == id:
            tareas_db[i] = tarea_actualizada
            return tarea_actualizada
    raise HTTPException(status_code=404, detail="La tarea no existe")

# 🗑️ DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea.id == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="La tarea no existe")

# 📊 GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for tarea in tareas_db:
        if tarea.estado in resumen:
            resumen[tarea.estado] += 1
    return resumen

# ✅ PUT /tareas/completar_todas
@app.put("/tareas/completar_todas")
def completar_todas():
    for tarea in tareas_db:
        tarea.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
