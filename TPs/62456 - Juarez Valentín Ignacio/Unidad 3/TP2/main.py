from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

# ----- MODELO DE DATOS -----
class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1)
    estado: str
    fecha_creacion: datetime

class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"

# ----- BASE DE DATOS EN MEMORIA -----
tareas: List[Tarea] = []
contador_id = 1
estados_validos = {"pendiente", "en_progreso", "completada"}


# ================== ENDPOINTS CRUD ==================

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    """
    GET /tareas
    Permite filtrar por estado o texto en la descripción.
    """
    resultado = tareas

    if estado:
        if estado not in estados_validos:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]

    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]

    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCrear):
    """
    POST /tareas
    Crea una nueva tarea validando que la descripción no esté vacía y el estado sea válido.
    """
    global contador_id

    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})

    if tarea.estado not in estados_validos:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion.strip(),
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: TareaCrear):
    """
    PUT /tareas/{id}
    Actualiza una tarea existente.
    """
    for t in tareas:
        if t.id == id:
            if not tarea_actualizada.descripcion.strip():
                raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
            if tarea_actualizada.estado not in estados_validos:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

            t.descripcion = tarea_actualizada.descripcion.strip()
            t.estado = tarea_actualizada.estado
            return t

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    DELETE /tareas/{id}
    Elimina una tarea existente.
    """
    for t in tareas:
        if t.id == id:
            tareas.remove(t)
            return {"mensaje": "Tarea eliminada exitosamente"}

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


# ================== FUNCIONALIDADES EXTRA ==================

@app.get("/tareas/resumen")
def resumen_tareas():
    """
    GET /tareas/resumen
    Devuelve el conteo de tareas por estado.
    """
    resumen = {estado: 0 for estado in estados_validos}
    for t in tareas:
        resumen[t.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    """
    PUT /tareas/completar_todas
    Marca todas las tareas como completadas.
    """
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}

    for t in tareas:
        t.estado = "completada"

    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
