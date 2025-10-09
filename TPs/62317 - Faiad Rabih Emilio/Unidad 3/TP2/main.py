import fastapi
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import datetime
from fastapi import HTTPException


class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fechacreada: str

estadosValidos = {"pendiente", "en_progreso", "completada"}
tareas: List[Tarea] = []

app = FastAPI()

@app.get("/")
async def Bienvenida():
    return {"mensaje": "guh"}

@app.get("/tareas")
async def VomitarTareas():
    return tareas

@app.post("/tareas")
async def CrearTarea(ID: int, DESCRIPCION: str, ESTADO: str):
    if ESTADO not in estadosValidos:
        raise HTTPException(status_code=422, detail="Estado inválido")
    nueva_tarea = Tarea(id=ID, descripcion=DESCRIPCION, estado=ESTADO, fechacreada=datetime.datetime.now().isoformat())
    tareas.append(nueva_tarea)
    return nueva_tarea


@app.put("/tareas/{ID}")
async def ModificarTarea(ID: int, DESCRIPCION: str, ESTADO: str):
    if ESTADO not in estadosValidos:
        raise HTTPException(status_code=422, detail="Estado inválido")
    for tarea in tareas:
        if tarea.id == ID:
            tarea.descripcion = DESCRIPCION
            tarea.estado = ESTADO
            return tarea
    return {"error": "Tarea no encontrada"}


@app.delete("/tareas/{ID}")
async def BorrarTarea(ID: int):
    for tarea in tareas:
        if tarea.id == ID:
            tareas.remove(tarea)
            return {"mensaje": "Tarea eliminada"}
    return {"error": "Tarea no encontrada"}