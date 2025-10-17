from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="Mini API de Tareas - TP2 Corregido")

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str


class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1, description="La descripción no puede estar vacía")
    estado: Optional[str] = Field("pendiente", description="Estado de la tarea (pendiente, en_progreso, completada)")


class TareaModificar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None



tareas: List[Tarea] = []
contador_id = 1



@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}



@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas

    if estado:
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]

    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]

    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(data: TareaCrear):
    global contador_id

    descripcion = data.descripcion.strip()
    estado = data.estado.strip() if data.estado else "pendiente"

    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    tarea = Tarea(
        id=contador_id,
        descripcion=descripcion,
        estado=estado,
        fecha_creacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    tareas.append(tarea)
    contador_id += 1
    return tarea



@app.put("/tareas/{id}")
def modificar_tarea(id: int, data: TareaModificar):
    for t in tareas:
        if t.id == id:
            if data.descripcion is not None:
                if not data.descripcion.strip():
                    raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
                t.descripcion = data.descripcion.strip()
            if data.estado is not None:
                if data.estado not in ["pendiente", "en_progreso", "completada"]:
                    raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
                t.estado = data.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas:
        if t.id == id:
            tareas.remove(t)
            return {"mensaje": f"Tarea {id} eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})



@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {
        "pendiente": sum(1 for t in tareas if t.estado == "pendiente"),
        "en_progreso": sum(1 for t in tareas if t.estado == "en_progreso"),
        "completada": sum(1 for t in tareas if t.estado == "completada")
    }
    return resumen



@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas:
        raise HTTPException(status_code=400, detail={"error": "No hay tareas para completar"})
    for t in tareas:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
