from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import sqlite3

from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoConTareas,
    TareaCreate, TareaUpdate, TareaResponse,
    EstadisticasProyecto, ResumenGeneral
)
from database import (
    init_db,
    crear_proyecto, obtener_proyectos, obtener_proyecto_por_id,
    contar_tareas_proyecto, actualizar_proyecto, eliminar_proyecto,
    crear_tarea, obtener_tareas, obtener_tarea_por_id,
    actualizar_tarea, eliminar_tarea,
    obtener_estadisticas_proyecto, obtener_resumen_general
)

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="API para manejar proyectos con tareas asociadas",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    init_db()
    print("🚀 API iniciada correctamente")

@app.get("/", tags=["General"])
async def root():
    return {
        "mensaje": "Bienvenido a la API de Gestión de Proyectos y Tareas",
        "version": "1.0.0",
        "documentacion": "/docs"
    }

# ==========================================
# ENDPOINTS DE PROYECTOS
# ==========================================

@app.get("/proyectos", response_model=list[ProyectoResponse], tags=["Proyectos"])
async def listar_proyectos(
    nombre: Optional[str] = Query(None, description="Filtrar proyectos por nombre")
):
    proyectos = obtener_proyectos(filtro_nombre=nombre)
    return proyectos

@app.get("/proyectos/{id}", response_model=ProyectoConTareas, tags=["Proyectos"])
async def obtener_proyecto(id: int):
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    proyecto["total_tareas"] = contar_tareas_proyecto(id)
    return proyecto

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201, tags=["Proyectos"])
async def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    if not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del proyecto no puede estar vacío")
    try:
        nuevo_proyecto = crear_proyecto(nombre=proyecto.nombre, descripcion=proyecto.descripcion)
        return nuevo_proyecto
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'")

@app.put("/proyectos/{id}", response_model=ProyectoResponse, tags=["Proyectos"])
async def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    proyecto_existente = obtener_proyecto_por_id(id)
    if not proyecto_existente:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    if proyecto.nombre is not None and not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del proyecto no puede estar vacío")
    
    try:
        actualizado = actualizar_proyecto(id, nombre=proyecto.nombre, descripcion=proyecto.descripcion)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        return obtener_proyecto_por_id(id)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'")

@app.delete("/proyectos/{id}", tags=["Proyectos"])
async def eliminar_proyecto_endpoint(id: int):
    eliminado = eliminar_proyecto(id)
    if not eliminado:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    return {"mensaje": f"Proyecto {id} y sus tareas eliminados correctamente"}

# ==========================================
# ENDPOINTS DE TAREAS
# ==========================================

@app.get("/tareas", response_model=list[TareaResponse], tags=["Tareas"])
async def listar_todas_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: str = Query("desc", description="Orden por fecha: 'asc' o 'desc'")
):
    tareas = obtener_tareas(proyecto_id=proyecto_id, estado=estado, prioridad=prioridad, orden=orden)
    return tareas

@app.get("/proyectos/{id}/tareas", response_model=list[TareaResponse], tags=["Tareas"])
async def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    orden: str = Query("desc", description="Orden por fecha: 'asc' o 'desc'")
):
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    tareas = obtener_tareas(proyecto_id=id, estado=estado, prioridad=prioridad, orden=orden)
    return tareas

@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201, tags=["Tareas"])
async def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción de la tarea no puede estar vacía")
    
    nueva_tarea = crear_tarea(
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        prioridad=tarea.prioridad,
        proyecto_id=id
    )
    return nueva_tarea

@app.put("/tareas/{id}", response_model=TareaResponse, tags=["Tareas"])
async def modificar_tarea(id: int, tarea: TareaUpdate):
    tarea_existente = obtener_tarea_por_id(id)
    if not tarea_existente:
        raise HTTPException(status_code=404, detail=f"Tarea con ID {id} no encontrada")
    
    if tarea.descripcion is not None and not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción de la tarea no puede estar vacía")
    
    if tarea.proyecto_id is not None:
        proyecto = obtener_proyecto_por_id(tarea.proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=400, detail=f"El proyecto con ID {tarea.proyecto_id} no existe")
    
    actualizado = actualizar_tarea(
        id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        prioridad=tarea.prioridad,
        proyecto_id=tarea.proyecto_id
    )
    
    if not actualizado:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    return obtener_tarea_por_id(id)

@app.delete("/tareas/{id}", tags=["Tareas"])
async def eliminar_tarea_endpoint(id: int):
    eliminado = eliminar_tarea(id)
    if not eliminado:
        raise HTTPException(status_code=404, detail=f"Tarea con ID {id} no encontrada")
    return {"mensaje": f"Tarea {id} eliminada correctamente"}

# ==========================================
# ENDPOINTS DE ESTADÍSTICAS
# ==========================================

@app.get("/proyectos/{id}/resumen", response_model=EstadisticasProyecto, tags=["Estadísticas"])
async def obtener_resumen_proyecto(id: int):
    estadisticas = obtener_estadisticas_proyecto(id)
    if not estadisticas:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    return estadisticas

@app.get("/resumen", response_model=ResumenGeneral, tags=["Estadísticas"])
async def obtener_resumen():
    resumen = obtener_resumen_general()
    return resumen