from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import sqlite3

from models import (
    ProyectoCreate, ProyectoUpdate, Proyecto, ProyectoConTareas,
    TareaCreate, TareaUpdate, Tarea, TareaConProyecto,
    ResumenProyecto, ResumenGeneral
)
from database import (
    init_db, crear_proyecto, obtener_proyectos, obtener_proyecto_por_id,
    actualizar_proyecto, eliminar_proyecto, proyecto_existe, nombre_proyecto_existe,
    crear_tarea, obtener_tareas, obtener_tareas_por_proyecto, obtener_tarea_por_id,
    actualizar_tarea, eliminar_tarea, obtener_resumen_proyecto, obtener_resumen_general,
    DB_NAME
)


app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    version="2.0",
    description="API con relaciones entre tablas y filtros avanzados"
)


# ============== EVENTOS DE LA APLICACIÓN ==============

@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar la aplicación"""
    init_db()


# ============== ENDPOINT RAÍZ ==============

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API de Gestión de Proyectos y Tareas",
        "version": "2.0",
        "endpoints_proyectos": {
            "GET /proyectos": "Lista todos los proyectos",
            "GET /proyectos/{id}": "Obtiene un proyecto específico",
            "POST /proyectos": "Crea un nuevo proyecto",
            "PUT /proyectos/{id}": "Modifica un proyecto",
            "DELETE /proyectos/{id}": "Elimina un proyecto y sus tareas",
            "GET /proyectos/{id}/tareas": "Lista tareas de un proyecto",
            "POST /proyectos/{id}/tareas": "Crea tarea en un proyecto",
            "GET /proyectos/{id}/resumen": "Estadísticas del proyecto"
        },
        "endpoints_tareas": {
            "GET /tareas": "Lista todas las tareas",
            "PUT /tareas/{id}": "Modifica una tarea",
            "DELETE /tareas/{id}": "Elimina una tarea"
        },
        "endpoints_resumen": {
            "GET /resumen": "Resumen general de la aplicación"
        }
    }


# ============== ENDPOINTS DE PROYECTOS ==============

@app.get("/proyectos", response_model=list[Proyecto])
async def listar_proyectos(
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)")
):
    """
    Lista todos los proyectos.
    
    - **nombre**: Filtra proyectos cuyo nombre contenga este texto
    """
    proyectos = obtener_proyectos(nombre=nombre)
    return proyectos


@app.get("/proyectos/{proyecto_id}", response_model=ProyectoConTareas)
async def obtener_proyecto(proyecto_id: int):
    """
    Obtiene un proyecto específico con el contador de tareas asociadas.
    """
    proyecto = obtener_proyecto_por_id(proyecto_id)
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return proyecto


@app.post("/proyectos", response_model=Proyecto, status_code=201)
async def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto.
    
    - **nombre**: Nombre del proyecto (único, no puede estar vacío)
    - **descripcion**: Descripción opcional del proyecto
    """
    # Verificar que el nombre no exista
    if nombre_proyecto_existe(proyecto.nombre):
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )
    
    try:
        nuevo_proyecto = crear_proyecto(
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion
        )
        return nuevo_proyecto
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un proyecto con ese nombre"
        )


@app.put("/proyectos/{proyecto_id}", response_model=Proyecto)
async def modificar_proyecto(proyecto_id: int, proyecto_update: ProyectoUpdate):
    """
    Modifica un proyecto existente.
    
    Puedes actualizar el nombre y/o la descripción.
    """
    # Verificar que el proyecto existe
    if not proyecto_existe(proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Si se está actualizando el nombre, verificar que no esté duplicado
    if proyecto_update.nombre and nombre_proyecto_existe(proyecto_update.nombre, excluir_id=proyecto_id):
        raise HTTPException(
            status_code=409,
            detail="Ya existe otro proyecto con ese nombre"
        )
    
    try:
        proyecto_actualizado = actualizar_proyecto(
            proyecto_id=proyecto_id,
            nombre=proyecto_update.nombre,
            descripcion=proyecto_update.descripcion
        )
        return proyecto_actualizado
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe otro proyecto con ese nombre"
        )


@app.delete("/proyectos/{proyecto_id}")
async def eliminar_proyecto_endpoint(proyecto_id: int):
    """
    Elimina un proyecto y todas sus tareas asociadas (CASCADE).
    """
    # Contar tareas antes de eliminar
    import sqlite3
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_count = cursor.fetchone()[0]
    conn.close()
    
    if not eliminar_proyecto(proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {
        "mensaje": "Proyecto eliminado correctamente",
        "tareas_eliminadas": tareas_count
    }


# ============== ENDPOINTS DE TAREAS ==============

@app.get("/tareas", response_model=list[TareaConProyecto])
async def listar_todas_las_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: str = Query("asc", description="Orden por fecha: asc o desc")
):
    """
    Lista todas las tareas de todos los proyectos con filtros opcionales.
    
    - **estado**: pendiente, en_progreso o completada
    - **prioridad**: baja, media o alta
    - **proyecto_id**: ID del proyecto
    - **orden**: asc (ascendente) o desc (descendente)
    
    Los filtros se pueden combinar.
    """
    tareas = obtener_tareas(
        estado=estado,
        prioridad=prioridad,
        proyecto_id=proyecto_id,
        orden=orden
    )
    return tareas


@app.get("/proyectos/{proyecto_id}/tareas", response_model=list[Tarea])
async def listar_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    orden: str = Query("asc", description="Orden por fecha: asc o desc")
):
    """
    Lista todas las tareas de un proyecto específico.
    
    - **estado**: pendiente, en_progreso o completada
    - **prioridad**: baja, media o alta
    - **orden**: asc (ascendente) o desc (descendente)
    """
    # Verificar que el proyecto existe
    if not proyecto_existe(proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    tareas = obtener_tareas_por_proyecto(
        proyecto_id=proyecto_id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    return tareas


@app.post("/proyectos/{proyecto_id}/tareas", response_model=Tarea, status_code=201)
async def crear_tarea_en_proyecto(proyecto_id: int, tarea: TareaCreate):
    """
    Crea una nueva tarea dentro de un proyecto.
    
    - **descripcion**: Descripción de la tarea (no puede estar vacía)
    - **estado**: pendiente, en_progreso o completada (default: pendiente)
    - **prioridad**: baja, media o alta (default: media)
    """
    # Verificar que el proyecto existe
    if not proyecto_existe(proyecto_id):
        raise HTTPException(
            status_code=400,
            detail="El proyecto especificado no existe"
        )
    
    nueva_tarea = crear_tarea(
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        prioridad=tarea.prioridad,
        proyecto_id=proyecto_id
    )
    return nueva_tarea


@app.put("/tareas/{tarea_id}", response_model=Tarea)
async def modificar_tarea(tarea_id: int, tarea_update: TareaUpdate):
    """
    Modifica una tarea existente.
    
    Puedes actualizar cualquier campo, incluyendo mover la tarea a otro proyecto.
    """
    # Verificar que la tarea existe
    tarea_actual = obtener_tarea_por_id(tarea_id)
    
    if not tarea_actual:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Si se está cambiando el proyecto, verificar que existe
    if tarea_update.proyecto_id is not None and not proyecto_existe(tarea_update.proyecto_id):
        raise HTTPException(
            status_code=400,
            detail="El proyecto especificado no existe"
        )
    
    tarea_actualizada = actualizar_tarea(
        tarea_id=tarea_id,
        descripcion=tarea_update.descripcion,
        estado=tarea_update.estado,
        prioridad=tarea_update.prioridad,
        proyecto_id=tarea_update.proyecto_id
    )
    
    return tarea_actualizada


@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea_endpoint(tarea_id: int):
    """
    Elimina una tarea.
    """
    if not eliminar_tarea(tarea_id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return {"mensaje": "Tarea eliminada correctamente"}


# ============== ENDPOINTS DE RESUMEN ==============

@app.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyecto)
async def obtener_resumen_proyecto_endpoint(proyecto_id: int):
    """
    Devuelve estadísticas detalladas de un proyecto.
    
    Incluye:
    - Total de tareas
    - Distribución por estado
    - Distribución por prioridad
    """
    resumen = obtener_resumen_proyecto(proyecto_id)
    
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return resumen


@app.get("/resumen", response_model=ResumenGeneral)
async def obtener_resumen_general_endpoint():
    """
    Devuelve un resumen general de toda la aplicación.
    
    Incluye:
    - Total de proyectos
    - Total de tareas
    - Distribución de tareas por estado
    - Proyecto con más tareas
    """
    resumen = obtener_resumen_general()
    return resumen


# ============== PUNTO DE ENTRADA ==============

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)