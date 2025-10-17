from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Mini API de tareas - TP2")

# MODELOS

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[str] = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
        if v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

# DATOS EN MEMORIA

tareas_db: List[Tarea] = []
contador_id = 1

ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

@app.get("/")
def root():
    return {"mensaje": "API de tareas - Trabajo Practico N° 2"}

# RUTAS CRUD

@app.get("/tareas/resumen")
def resumen_tareas_db():
    """
    Devuelve el conteo de tareas_db por estado
    """
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas_db:
        resumen[tarea.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas_db como completadas
    """
    if not tareas_db:
        return {"mensaje": "No hay tareas_db para completar"}

    for tarea in tareas_db:
        tarea.estado = "completada"

    return {"mensaje": "Todas las tareas_db fueron completadas exitosamente"}


@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas_db(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    """
    Devuelve todas las tareas_db o filtra por estado y/o texto en la descripción
    """
    resultado = tareas_db

    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]

    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]

    return resultado


@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crear una nueva tarea validando estado y descripción
    """
    global contador_id

    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1

    return nueva_tarea


@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, datos: TareaUpdate):
    """
    Actualiza una tarea existente
    """
    for tarea in tareas_db:
        if tarea.id == id:
            if datos.descripcion is not None:
                if not datos.descripcion.strip():
                    raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
                tarea.descripcion = datos.descripcion
            if datos.estado is not None:
                if datos.estado not in ESTADOS_VALIDOS:
                    raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
                tarea.estado = datos.estado
            return tarea

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea según su ID
    """
    for tarea in tareas_db:
        if tarea.id == id:
            tareas_db.remove(tarea)
            return {"mensaje": "Tarea eliminada exitosamente"}

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
