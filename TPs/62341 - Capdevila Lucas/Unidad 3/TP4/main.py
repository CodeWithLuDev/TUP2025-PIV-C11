"""
TP4: API de Gestión de Proyectos y Tareas
Relaciones entre tablas y filtros avanzados con FastAPI y SQLite
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse

from models import (
    ProyectoCreate, ProyectoUpdate, Proyecto,
    TareaCreate, TareaUpdate, Tarea
)
from database import (
    init_db,
    crear_proyecto, obtener_proyectos, obtener_proyecto, actualizar_proyecto, eliminar_proyecto,
    crear_tarea, obtener_tareas, obtener_tarea, actualizar_tarea, eliminar_tarea,
    obtener_resumen_proyecto, obtener_resumen_general
)


app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="API REST con relaciones entre tablas usando SQLite y FastAPI",
    version="2.0.0",
)

# Inicializar base de datos al arrancar
init_db()


# ========== ENDPOINT RAÍZ ==========

@app.get("/")
async def raiz():
    """Información general de la API"""
    return {
        "nombre": "API de Gestión de Proyectos y Tareas",
        "version": "2.0.0",
        "descripcion": "API REST con relaciones 1:N entre proyectos y tareas",
        "endpoints": {
            "GET /": "Información de la API",
            "GET /proyectos": "Lista todos los proyectos",
            "GET /proyectos/{id}": "Obtiene un proyecto específico",
            "POST /proyectos": "Crea un nuevo proyecto",
            "PUT /proyectos/{id}": "Modifica un proyecto",
            "DELETE /proyectos/{id}": "Elimina un proyecto y sus tareas",
            "GET /proyectos/{id}/tareas": "Lista tareas de un proyecto",
            "POST /proyectos/{id}/tareas": "Crea tarea en un proyecto",
            "GET /proyectos/{id}/resumen": "Estadísticas del proyecto",
            "GET /tareas": "Lista todas las tareas",
            "GET /tareas/{id}": "Obtiene una tarea específica",
            "PUT /tareas/{id}": "Modifica una tarea",
            "DELETE /tareas/{id}": "Elimina una tarea",
            "GET /resumen": "Resumen general de la aplicación"
        }
    }


# ========== ENDPOINTS DE PROYECTOS ==========

@app.get("/proyectos", response_model=list[Proyecto])
async def listar_proyectos(
    nombre: Optional[str] = Query(default=None, description="Filtrar por nombre parcial")
):
    """Lista todos los proyectos con contador de tareas"""
    proyectos = obtener_proyectos(filtro_nombre=nombre)
    return proyectos


@app.get("/proyectos/{proyecto_id}", response_model=Proyecto)
async def obtener_proyecto_detalle(proyecto_id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    proyecto = obtener_proyecto(proyecto_id)
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Proyecto no encontrado"}
        )
    return proyecto


@app.post("/proyectos", response_model=Proyecto, status_code=status.HTTP_201_CREATED)
async def crear_proyecto_endpoint(payload: ProyectoCreate):
    """Crea un nuevo proyecto"""
    fecha_creacion = datetime.now(timezone.utc).isoformat()
    
    proyecto = crear_proyecto(
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        fecha_creacion=fecha_creacion
    )
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Ya existe un proyecto con ese nombre"}
        )
    
    return proyecto


@app.put("/proyectos/{proyecto_id}", response_model=Proyecto)
async def actualizar_proyecto_endpoint(proyecto_id: int, payload: ProyectoUpdate):
    """Modifica un proyecto existente"""
    proyecto = actualizar_proyecto(
        proyecto_id=proyecto_id,
        nombre=payload.nombre,
        descripcion=payload.descripcion
    )
    
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Proyecto no encontrado"}
        )
    
    return proyecto


@app.delete("/proyectos/{proyecto_id}")
async def eliminar_proyecto_endpoint(proyecto_id: int):
    """Elimina un proyecto y todas sus tareas (CASCADE)"""
    eliminado, tareas_eliminadas = eliminar_proyecto(proyecto_id)
    
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Proyecto no encontrado"}
        )
    
    return {
        "mensaje": "Proyecto y sus tareas eliminados correctamente",
        "tareas_eliminadas": tareas_eliminadas
    }


# ========== ENDPOINTS DE TAREAS ==========

@app.get("/proyectos/{proyecto_id}/tareas", response_model=list[Tarea])
async def listar_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default=None)
):
    """Lista todas las tareas de un proyecto específico"""
    # Verificar que el proyecto existe
    proyecto = obtener_proyecto(proyecto_id)
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Proyecto no encontrado"}
        )
    
    # Validar filtros
    if estado is not None and estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Estado inválido"}
        )
    
    if prioridad is not None and prioridad not in ["baja", "media", "alta"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Prioridad inválida"}
        )
    
    tareas = obtener_tareas(
        proyecto_id=proyecto_id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    return tareas


@app.post("/proyectos/{proyecto_id}/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
async def crear_tarea_proyecto(proyecto_id: int, payload: TareaCreate):
    """Crea una tarea dentro de un proyecto"""
    # Verificar que el proyecto existe
    proyecto = obtener_proyecto(proyecto_id)
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Proyecto no encontrado"}
        )
    
    fecha_creacion = datetime.now(timezone.utc).isoformat()
    
    tarea = crear_tarea(
        descripcion=payload.descripcion,
        estado=payload.estado,
        prioridad=payload.prioridad,
        proyecto_id=proyecto_id,
        fecha_creacion=fecha_creacion
    )
    
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Error al crear la tarea"}
        )
    
    return tarea


@app.get("/tareas", response_model=list[Tarea])
async def listar_todas_tareas(
    proyecto_id: Optional[int] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default=None)
):
    """Lista todas las tareas de todos los proyectos con filtros opcionales"""
    # Validar filtros
    if estado is not None and estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Estado inválido"}
        )
    
    if prioridad is not None and prioridad not in ["baja", "media", "alta"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Prioridad inválida"}
        )
    
    tareas = obtener_tareas(
        proyecto_id=proyecto_id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    return tareas


@app.get("/tareas/{tarea_id}", response_model=Tarea)
async def obtener_tarea_detalle(tarea_id: int):
    """Obtiene una tarea específica"""
    tarea = obtener_tarea(tarea_id)
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Tarea no encontrada"}
        )
    return tarea


@app.put("/tareas/{tarea_id}", response_model=Tarea)
async def actualizar_tarea_endpoint(tarea_id: int, payload: TareaUpdate):
    """Modifica una tarea existente (puede cambiar de proyecto)"""
    tarea = actualizar_tarea(
        tarea_id=tarea_id,
        descripcion=payload.descripcion,
        estado=payload.estado,
        prioridad=payload.prioridad,
        proyecto_id=payload.proyecto_id
    )
    
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Tarea o proyecto no encontrado"}
        )
    
    return tarea


@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea_endpoint(tarea_id: int):
    """Elimina una tarea"""
    eliminado = eliminar_tarea(tarea_id)
    
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Tarea no encontrada"}
        )
    
    return {"mensaje": "Tarea eliminada correctamente"}


# ========== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==========

@app.get("/proyectos/{proyecto_id}/resumen")
async def resumen_proyecto(proyecto_id: int):
    """Devuelve estadísticas de un proyecto específico"""
    resumen = obtener_resumen_proyecto(proyecto_id)
    
    if not resumen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Proyecto no encontrado"}
        )
    
    return resumen


@app.get("/resumen")
async def resumen_general():
    """Resumen general de toda la aplicación"""
    return obtener_resumen_general()


# ========== EJECUCIÓN ==========

if __name__ == "__main__":
    import uvicorn

    print("=== API DE GESTIÓN DE PROYECTOS Y TAREAS ===")
    print("Visita: http://127.0.0.1:8000/")
    print("Documentación: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)