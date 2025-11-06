from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Literal
import sqlite3
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse
)
from database import (
    init_db, get_db_connection,
    crear_proyecto, obtener_proyectos, obtener_proyecto_por_id,
    actualizar_proyecto, eliminar_proyecto, proyecto_existe,
    crear_tarea, obtener_tareas, obtener_tarea_por_id,
    actualizar_tarea, eliminar_tarea,
    obtener_resumen_proyecto, obtener_resumen_general
)

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="API RESTful para gestionar proyectos con sus tareas asociadas",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    """Inicializa la base de datos al iniciar la aplicación"""
    init_db()
    print("✅ Base de datos inicializada correctamente")


# ==================== ENDPOINTS DE PROYECTOS ====================

@app.get("/proyectos", response_model=list[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)")):
    """
    Lista todos los proyectos con contador de tareas.
    Opcionalmente filtra por nombre.
    """
    try:
        proyectos = obtener_proyectos(nombre)
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")


@app.get("/proyectos/{id}", response_model=ProyectoResponse)
def obtener_proyecto(id: int):
    """
    Obtiene un proyecto específico por su ID con contador de tareas.
    """
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto.
    El nombre debe ser único y no puede estar vacío.
    """
    try:
        nuevo_proyecto = crear_proyecto(proyecto.nombre, proyecto.descripcion)
        return nuevo_proyecto
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear proyecto: {str(e)}")


@app.put("/proyectos/{id}", response_model=ProyectoResponse)
def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    """
    Modifica un proyecto existente.
    Se pueden actualizar el nombre y/o la descripción.
    """
    # Verificar que el proyecto existe
    if not obtener_proyecto_por_id(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        actualizar_proyecto(id, proyecto.nombre, proyecto.descripcion)
        proyecto_actualizado = obtener_proyecto_por_id(id)
        return proyecto_actualizado
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar proyecto: {str(e)}")


@app.delete("/proyectos/{id}")
def eliminar_proyecto_endpoint(id: int):
    """
    Elimina un proyecto y todas sus tareas asociadas (CASCADE).
    """
    if not obtener_proyecto_por_id(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        eliminar_proyecto(id)
        return {"mensaje": "Proyecto y sus tareas eliminados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar proyecto: {str(e)}")


# ==================== ENDPOINTS DE TAREAS ====================

@app.get("/tareas", response_model=list[TareaResponse])
def listar_todas_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: Literal["asc", "desc"] = Query("asc", description="Ordenar por fecha de creación")
):
    """
    Lista todas las tareas de todos los proyectos.
    Soporta filtros múltiples y ordenamiento.
    """
    try:
        tareas = obtener_tareas(proyecto_id, estado, prioridad, orden)
        return tareas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@app.get("/proyectos/{id}/tareas", response_model=list[TareaResponse])
def listar_tareas_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None, description="Filtrar por prioridad"),
    orden: Literal["asc", "desc"] = Query("asc", description="Ordenar por fecha de creación")
):
    """
    Lista todas las tareas de un proyecto específico.
    Soporta filtros por estado, prioridad y ordenamiento.
    """
    # Verificar que el proyecto existe
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        tareas = obtener_tareas(id, estado, prioridad, orden)
        return tareas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """
    Crea una nueva tarea dentro de un proyecto.
    El proyecto debe existir.
    """
    # Verificar que el proyecto existe
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        nueva_tarea = crear_tarea(
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad,
            id
        )
        return obtener_tarea_por_id(nueva_tarea['id'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear tarea: {str(e)}")


@app.put("/tareas/{id}", response_model=TareaResponse)
def modificar_tarea(id: int, tarea: TareaUpdate):
    """
    Modifica una tarea existente.
    Puede cambiar descripción, estado, prioridad y/o proyecto.
    """
    # Verificar que la tarea existe
    if not obtener_tarea_por_id(id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Si se va a cambiar de proyecto, verificar que el nuevo proyecto existe
    if tarea.proyecto_id is not None and not proyecto_existe(tarea.proyecto_id):
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {tarea.proyecto_id} no existe"
        )
    
    try:
        actualizar_tarea(
            id,
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad,
            tarea.proyecto_id
        )
        tarea_actualizada = obtener_tarea_por_id(id)
        return tarea_actualizada
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar tarea: {str(e)}")


@app.delete("/tareas/{id}")
def eliminar_tarea_endpoint(id: int):
    """
    Elimina una tarea específica.
    """
    if not obtener_tarea_por_id(id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    try:
        eliminar_tarea(id)
        return {"mensaje": "Tarea eliminada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar tarea: {str(e)}")


# ==================== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ====================

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    """
    Devuelve estadísticas detalladas de un proyecto:
    - Total de tareas
    - Distribución por estado
    - Distribución por prioridad
    """
    resumen = obtener_resumen_proyecto(id)
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return resumen


@app.get("/resumen")
def resumen_general():
    """
    Devuelve estadísticas generales de toda la aplicación:
    - Total de proyectos
    - Total de tareas
    - Distribución de tareas por estado
    - Proyecto con más tareas
    """
    try:
        return obtener_resumen_general()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


# ==================== ENDPOINT DE SALUD ====================

@app.get("/")
def root():
    """
    Endpoint raíz para verificar que la API está funcionando.
    """
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


@app.get("/health")
def health_check():
    """
    Verifica el estado de salud de la API y la base de datos.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)