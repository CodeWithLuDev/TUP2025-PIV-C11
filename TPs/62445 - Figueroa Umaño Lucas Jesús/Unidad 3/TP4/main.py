from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Literal
import sqlite3

from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse,
    ResumenProyecto, ResumenGeneral,
    Mensaje, ErrorResponse
)
from database import (
    init_db,
    crear_proyecto, obtener_proyectos, obtener_proyecto,
    actualizar_proyecto, eliminar_proyecto, proyecto_existe,
    crear_tarea, obtener_tareas, obtener_tarea,
    actualizar_tarea, eliminar_tarea,
    obtener_resumen_proyecto, obtener_resumen_general
)

from database import DB_NAME

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="Sistema para administrar proyectos y sus tareas asociadas",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    print("🚀 API iniciada correctamente")


@app.get("/proyectos", response_model=list[ProyectoResponse], tags=["Proyectos"])
def listar_proyectos(
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)")
):
    """
    Lista todos los proyectos.
    
    - **nombre**: Filtra proyectos cuyo nombre contenga este texto (opcional)
    """
    proyectos = obtener_proyectos(nombre=nombre)
    return proyectos

@app.get("/proyectos/{id}", response_model=ProyectoResponse, tags=["Proyectos"])
def obtener_proyecto_por_id(id: int):
    """
    Obtiene un proyecto específico por su ID.
    
    Incluye el contador de tareas asociadas.
    """
    proyecto = obtener_proyecto(id)
    
    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el proyecto con ID {id}"
        )
    
    return proyecto

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201, tags=["Proyectos"])
def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto.
    
    - **nombre**: Nombre del proyecto (obligatorio, único)
    - **descripcion**: Descripción del proyecto (opcional)
    """
    try:
        proyecto_id = crear_proyecto(
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion
        )
     
        nuevo_proyecto = obtener_proyecto(proyecto_id)
        return nuevo_proyecto
        
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
            )
        raise HTTPException(status_code=400, detail="Error al crear el proyecto")

@app.put("/proyectos/{id}", response_model=ProyectoResponse, tags=["Proyectos"])
def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    """
    Modifica un proyecto existente.
    
    - **nombre**: Nuevo nombre del proyecto
    - **descripcion**: Nueva descripción del proyecto
    """
    if not proyecto_existe(id):
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el proyecto con ID {id}"
        )
    
    try:
        actualizado = actualizar_proyecto(
            proyecto_id=id,
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion
        )
        
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el proyecto")
        
        # Devolver el proyecto actualizado
        proyecto_actualizado = obtener_proyecto(id)
        return proyecto_actualizado
        
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
            )
        raise HTTPException(status_code=400, detail="Error al actualizar el proyecto")

@app.delete("/proyectos/{id}", response_model=Mensaje, tags=["Proyectos"])
def eliminar_proyecto_por_id(id: int):
    """
    Elimina un proyecto y todas sus tareas asociadas (CASCADE).
    """
    if not proyecto_existe(id):
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el proyecto con ID {id}"
        )
    
    # Contar tareas antes de eliminar
    tareas = obtener_tareas(proyecto_id=id)
    cantidad_tareas = len(tareas)
    
    eliminado = eliminar_proyecto(id)
    
    if not eliminado:
        raise HTTPException(status_code=400, detail="No se pudo eliminar el proyecto")
    
    return {
        "mensaje": f"Proyecto con ID {id} eliminado exitosamente junto con sus tareas",
        "tareas_eliminadas": cantidad_tareas  # ← AGREGAR ESTO
    }

@app.get("/tareas", response_model=list[TareaResponse], tags=["Tareas"])
def listar_todas_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: Literal["asc", "desc"] = Query("asc", description="Orden por fecha de creación")
):
    """
    Lista todas las tareas de todos los proyectos.
    
    Permite filtrar por:
    - **estado**: pendiente, en_progreso, completada
    - **prioridad**: baja, media, alta
    - **proyecto_id**: ID del proyecto
    - **orden**: asc (ascendente) o desc (descendente) por fecha de creación
    
    Los filtros se pueden combinar.
    """
    tareas = obtener_tareas(
        proyecto_id=proyecto_id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    return tareas

@app.get("/proyectos/{id}/tareas", response_model=list[TareaResponse], tags=["Tareas"])
def listar_tareas_de_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Literal["asc", "desc"] = Query("asc")
):
    """
    Lista todas las tareas de un proyecto específico.
    
    Permite filtrar por estado, prioridad y ordenar por fecha.
    """
    if not proyecto_existe(id):
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el proyecto con ID {id}"
        )
    
    tareas = obtener_tareas(
        proyecto_id=id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    return tareas

@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201, tags=["Tareas"])
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """
    Crea una nueva tarea dentro de un proyecto específico.
    
    - **descripcion**: Descripción de la tarea (obligatorio)
    - **estado**: Estado de la tarea (por defecto: pendiente)
    - **prioridad**: Prioridad de la tarea (por defecto: media)
    """
    if not proyecto_existe(id):
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {id} no existe"
        )
    
    try:
        tarea_id = crear_tarea(
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            proyecto_id=id
        )
        
        nueva_tarea = obtener_tarea(tarea_id)
        return nueva_tarea
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear la tarea: {str(e)}")

@app.put("/tareas/{id}", response_model=TareaResponse, tags=["Tareas"])
def modificar_tarea(id: int, tarea: TareaUpdate):
    """
    Modifica una tarea existente.
    
    Permite cambiar la tarea de proyecto modificando el proyecto_id.
    """
    tarea_actual = obtener_tarea(id)
    if not tarea_actual:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró la tarea con ID {id}"
        )
    
    # Usar valores actuales si no se proporcionan nuevos
    descripcion = tarea.descripcion if tarea.descripcion is not None else tarea_actual['descripcion']
    estado = tarea.estado if tarea.estado is not None else tarea_actual['estado']
    prioridad = tarea.prioridad if tarea.prioridad is not None else tarea_actual['prioridad']
    proyecto_id = tarea.proyecto_id if tarea.proyecto_id is not None else tarea_actual['proyecto_id']
    
    # Verificar que el proyecto existe
    if not proyecto_existe(proyecto_id):
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {proyecto_id} no existe"
        )
    
    try:
        actualizado = actualizar_tarea(
            tarea_id=id,
            descripcion=descripcion,
            estado=estado,
            prioridad=prioridad,
            proyecto_id=proyecto_id
        )
        
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la tarea")
        
        tarea_actualizada = obtener_tarea(id)
        return tarea_actualizada
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar la tarea: {str(e)}")
    
@app.delete("/tareas/{id}", response_model=Mensaje, tags=["Tareas"])
def eliminar_tarea_por_id(id: int):
    """
    Elimina una tarea específica.
    """
    if not obtener_tarea(id):
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró la tarea con ID {id}"
        )
    
    eliminado = eliminar_tarea(id)
    
    if not eliminado:
        raise HTTPException(status_code=400, detail="No se pudo eliminar la tarea")
    
    return {"mensaje": f"Tarea con ID {id} eliminada exitosamente"}

@app.get("/proyectos/{id}/resumen", response_model=ResumenProyecto, tags=["Estadísticas"])
def obtener_resumen_de_proyecto(id: int):
    """
    Obtiene estadísticas detalladas de un proyecto:
    
    - Total de tareas
    - Tareas por estado (pendiente, en_progreso, completada)
    - Tareas por prioridad (baja, media, alta)
    """
    resumen = obtener_resumen_proyecto(id)
    
    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el proyecto con ID {id}"
        )
    
    return resumen

@app.get("/resumen", response_model=ResumenGeneral, tags=["Estadísticas"])
def obtener_resumen_completo():
    """
    Obtiene un resumen general de toda la aplicación:
    
    - Total de proyectos
    - Total de tareas
    - Tareas por estado
    - Proyecto con más tareas
    """
    resumen = obtener_resumen_general()
    return resumen


@app.get("/", tags=["General"])
def raiz():
    """
    Endpoint raíz con información de la API.
    """
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas",
        "version": "1.0.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "documentacion": "/docs",
            "resumen": "/resumen"
        }
    }



@app.exception_handler(ValueError)
def value_error_handler(request, exc):
    """Maneja errores de validación"""
    return JSONResponse(
        status_code=400,
        content={"error": "Datos inválidos", "detalle": str(exc)}
    )

@app.exception_handler(sqlite3.IntegrityError)
def integrity_error_handler(request, exc):
    """Maneja errores de integridad de la base de datos"""
    return JSONResponse(
        status_code=409,
        content={"error": "Error de integridad", "detalle": str(exc)}
    )