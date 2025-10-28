from fastapi import FastAPI, HTTPException
from models import Tarea
import database

app = FastAPI(title="Mini API de Tareas")

@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}

@app.get("/tareas")
def listar_tareas():
    return database.obtener_todas()

@app.get("/tareas/{tarea_id}")
def obtener_tarea(tarea_id: int):
    tarea = database.obtener_por_id(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

@app.post("/tareas")
def crear_tarea(tarea: Tarea):
    nueva_tarea = tarea.dict()
    creada = database.crear_tarea(nueva_tarea)
    return creada

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    tarea = database.obtener_por_id(tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    database.eliminar_tarea(tarea_id)
    return {"mensaje": "Tarea eliminada correctamente"}
