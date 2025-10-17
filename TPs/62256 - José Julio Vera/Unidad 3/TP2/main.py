from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

class TareaIn(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = None

estadosValidos = {"pendiente", "en_progreso", "completada"}
tareas_db: List[Tarea] = []
contador_id = 1

app = FastAPI()

@app.get("/")
async def Bienvenida():
    return {"mensaje": "guh"}

@app.get("/tareas")
async def VomitarTareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    tareas = tareas_db
    if estado:
        if estado not in estadosValidos:
            raise HTTPException(status_code=400, detail="Estado inválido")
        tareas = [t for t in tareas if t.estado == estado]
    if texto:
        tareas = [t for t in tareas if texto.lower() in t.descripcion.lower()]
    return [tarea.model_dump() for tarea in tareas]

@app.post("/tareas", status_code=201)
async def CrearTarea(tarea_in: TareaIn):
    global contador_id
    descripcion = tarea_in.descripcion.strip()
    if not descripcion:
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
    estado = tarea_in.estado or "pendiente"
    if estado not in estadosValidos:
        raise HTTPException(status_code=422, detail="Estado inválido")
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=descripcion,
        estado=estado,
        fecha_creacion=datetime.datetime.now().isoformat()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea.model_dump()

@app.put("/tareas/completar_todas", status_code=200)
async def CompletarTodas():
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas"}
    for tarea in tareas_db:
        tarea.estado = "completada"
    return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.put("/tareas/{id}")
async def ModificarTarea(id: int, tarea_in: dict):
    for tarea in tareas_db:
        if tarea.id == id:
            descripcion = tarea_in.get("descripcion", tarea.descripcion)
            estado = tarea_in.get("estado", tarea.estado)
            if descripcion is not None and not descripcion.strip():
                descripcion = tarea.descripcion
            if estado is not None and estado not in estadosValidos:
                raise HTTPException(status_code=422, detail="Estado inválido")
            tarea.descripcion = descripcion
            tarea.estado = estado
            return tarea.model_dump()
    raise HTTPException(status_code=404, detail="error: Tarea no encontrada")

@app.delete("/tareas/{id}")
async def BorrarTarea(id: int):
    for tarea in tareas_db:
        if tarea.id == id:
            tareas_db.remove(tarea)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="error: Tarea no encontrada")

@app.get("/tareas/resumen")
async def ResumenTareas():
    resumen = {estado: 0 for estado in estadosValidos}
    for tarea in tareas_db:
        if tarea.estado in resumen:
            resumen[tarea.estado] += 1
    return resumen