from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI()


tareas_db: List["Tarea"] = []
id_counter = 1


ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}


class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(default="pendiente")


class Tarea(TareaCreate):
    id: int
    fecha_creacion: datetime


@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    global id_counter
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    nueva_tarea = Tarea(
        id=id_counter,
        descripcion=tarea.descripcion.strip(),
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    id_counter += 1
    return nueva_tarea


@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    if estado and estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas_db:
        resumen[tarea.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    for tarea in tareas_db:
        tarea.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}


@app.put("/tareas/{id}", response_model=Tarea)
def modificar_tarea(id: int, tarea_actualizada: TareaCreate):
    for tarea in tareas_db:
        if tarea.id == id:
            if tarea_actualizada.estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
            if not tarea_actualizada.descripcion.strip():
                raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
            tarea.descripcion = tarea_actualizada.descripcion.strip()
            tarea.estado = tarea_actualizada.estado
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea.id == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
