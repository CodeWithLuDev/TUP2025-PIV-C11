from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import sqlite3

from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse,
    ResumenProyecto, ResumenGeneral
)
from database import (
    init_db, DB_NAME,
    crear_proyecto, obtener_proyectos, obtener_proyecto_por_id,
    actualizar_proyecto, eliminar_proyecto,
    crear_tarea, obtener_tareas, obtener_tarea_por_id,
    actualizar_tarea, eliminar_tarea,
    obtener_resumen_proyecto, obtener_resumen_general
)

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="API para administrar proyectos y sus tareas asociadas",
    version="1.0.0"
)

# Inicializar la base de datos al iniciar la aplicación
@app.on_event("startup")
def startup_event():
    init_db()

#  ENDPOINTS DE PROYECTOS 

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto_endpoint(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    try:
        proyecto_creado = crear_proyecto(proyecto.nombre, proyecto.descripcion)
        return proyecto_creado
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.get("/proyectos", response_model=list[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None)):
    """Lista todos los proyectos o filtra por nombre"""
    proyectos = obtener_proyectos(nombre)
    return proyectos

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    proyecto = obtener_proyecto_por_id(proyecto_id, incluir_contador=True)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@app.put("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto_endpoint(proyecto_id: int, proyecto: ProyectoUpdate):
    """Actualiza un proyecto existente"""
    try:
        proyecto_actualizado = actualizar_proyecto(
            proyecto_id,
            proyecto.nombre,
            proyecto.descripcion
        )
        if not proyecto_actualizado:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return proyecto_actualizado
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto_endpoint(proyecto_id: int):
    """Elimina un proyecto y todas sus tareas asociadas"""
    resultado = eliminar_proyecto(proyecto_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resultado

#ENDPOINTS DE TAREAS

@app.post("/proyectos/{proyecto_id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea_endpoint(proyecto_id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto"""
    try:
        tarea_creada = crear_tarea(
            proyecto_id,
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad
        )
        return tarea_creada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/proyectos/{proyecto_id}/tareas", response_model=list[TareaResponse])
def listar_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    """Lista todas las tareas de un proyecto específico"""
    # Verificar que el proyecto existe
    proyecto = obtener_proyecto_por_id(proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    tareas = obtener_tareas(proyecto_id, estado, prioridad, orden)
    return tareas

@app.get("/tareas", response_model=list[TareaResponse])
def listar_todas_tareas(
    proyecto_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    """Lista todas las tareas con filtros opcionales"""
    tareas = obtener_tareas(proyecto_id, estado, prioridad, orden)
    return tareas

@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea_endpoint(tarea_id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    try:
        tarea_actualizada = actualizar_tarea(
            tarea_id,
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad,
            tarea.proyecto_id
        )
        if not tarea_actualizada:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        return tarea_actualizada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea_endpoint(tarea_id: int):
    """Elimina una tarea específica"""
    eliminada = eliminar_tarea(tarea_id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"mensaje": "Tarea eliminada exitosamente"}

# ENDPOINTS DE ESTADÍSTICAS 

@app.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyecto)
def obtener_resumen_proyecto_endpoint(proyecto_id: int):
    """Obtiene estadísticas detalladas de un proyecto"""
    resumen = obtener_resumen_proyecto(proyecto_id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resumen

@app.get("/resumen", response_model=ResumenGeneral)
def obtener_resumen_general_endpoint():
    """Obtiene resumen general de toda la aplicación"""
    resumen = obtener_resumen_general()
    return resumen

# ENDPOINT RAÍZ 

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas",
        "version": "1.0.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen",
            "documentacion": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)