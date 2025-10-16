from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI()

tareas_db = []
contador_id = 1

class Task(BaseModel):
    id: Optional[int] = None
    descripcion: Optional[str] = None
    estado: str = "pendiente"
    fecha_creacion: Optional[datetime] = None

@app.get("/tareas", response_model=List[Task])
async def get_tasks(estado: Optional[str] = None, texto: Optional[str] = None):
    result = tareas_db
    if estado:
        result = [task for task in result if task.estado == estado]
    if texto:
        result = [task for task in result if texto.lower() in task.descripcion.lower()]
    return result

@app.post("/tareas", response_model=Task, status_code=201)
async def create_task(task: Task):
    global contador_id
    if not task.descripcion or not task.descripcion.strip():
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
    if task.estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(status_code=422, detail="Estado inválido")
    task.id = contador_id
    task.fecha_creacion = datetime.now()
    tareas_db.append(task)
    contador_id += 1
    return task

@app.get("/tareas/resumen", response_model=dict)
async def get_summary():
    summary = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for task in tareas_db:
        summary[task.estado] += 1
    return summary

@app.put("/tareas/completar_todas", response_model=dict)
async def complete_all_tasks():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for task in tareas_db:
        task.estado = "completada"
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

@app.put("/tareas/{id}", response_model=Task)
async def update_task(id: int, task_update: Task):
    for task in tareas_db:
        if task.id == id:
            if task_update.descripcion and task_update.descripcion.strip():
                task.descripcion = task_update.descripcion
            if task_update.estado:
                if task_update.estado not in ["pendiente", "en_progreso", "completada"]:
                    raise HTTPException(status_code=422, detail="Estado inválido")
                task.estado = task_update.estado
            return task
    raise HTTPException(status_code=404, detail="error: La tarea no existe")

@app.delete("/tareas/{id}", response_model=dict)
async def delete_task(id: int):
    for i, task in enumerate(tareas_db):
        if task.id == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="error: La tarea no existe")