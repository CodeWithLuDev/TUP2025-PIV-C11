from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# Estados válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

# Modelos
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(..., pattern="^(pendiente|en_progreso|completada)$")

# Datos en memoria
tareas: List[Tarea] = []
contador_id = 1

# GET /tareas (con filtros)
@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return JSONResponse(status_code=400, content={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# POST /tareas
@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaInput):
    global contador_id
    if not tarea.descripcion.strip():
        return JSONResponse(status_code=400, content={"error": "La descripción no puede estar vacía"})
    if tarea.estado not in ESTADOS_VALIDOS:
        return JSONResponse(status_code=400, content={"error": "Estado inválido"})
    nueva = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva)
    contador_id += 1
    return nueva

# PUT /tareas/{id}
@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaInput):
    for t in tareas:
        if t.id == id:
            if not tarea.descripcion.strip():
                return JSONResponse(status_code=400, content={"error": "La descripción no puede estar vacía"})
            if tarea.estado not in ESTADOS_VALIDOS:
                return JSONResponse(status_code=400, content={"error": "Estado inválido"})
            t.descripcion = tarea.descripcion
            t.estado = tarea.estado
            return t
    return JSONResponse(status_code=404, content={"error": "La tarea no existe"})

# DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, t in enumerate(tareas):
        if t.id == id:
            tareas.pop(i)
            return {"mensaje": "Tarea eliminada"}
    return JSONResponse(status_code=404, content={"error": "La tarea no existe"})

# GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas:
        resumen[t.estado] += 1
    return resumen

# PUT /tareas/completar_todas
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas:
        return JSONResponse(status_code=200, content={"mensaje": "No hay tareas para completar"})
    for t in tareas:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# GET raíz opcional
@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}