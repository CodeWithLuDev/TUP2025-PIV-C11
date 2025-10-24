from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Literal
import sqlite3
import sys

# Verificar que sqlite3 esté disponible
try:
    import sqlite3
    print(f"SQLite3 version: {sqlite3.sqlite_version}")
except ImportError:
    print("ERROR: SQLite3 no está disponible en esta instalación de Python")
    sys.exit(1)

from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse,
    ResumenProyecto, ResumenGeneral
)
from database import (
    init_db, crear_proyecto, obtener_proyectos, obtener_proyecto,
    actualizar_proyecto, eliminar_proyecto, proyecto_existe,
    crear_tarea, obtener_tareas, obtener_tarea, actualizar_tarea,
    eliminar_tarea, obtener_resumen_proyecto, obtener_resumen_general,
    DB_NAME
)

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="TP4 - API con relaciones entre tablas usando SQLite",
    version="1.0.0"
)

# Inicializar la base de datos al arrancar
@app.on_event("startup")
async def startup():
    print("Iniciando aplicación...")
    init_db()
    print("Base de datos inicializada correctamente")


# ========== ENDPOINTS DE PROYECTOS ==========

@app.get("/proyectos")
async def listar_proyectos(nombre: Optional[str] = Query(None, description="Buscar proyectos por nombre")):
    """Lista todos los proyectos, opcionalmente filtrados por nombre."""
    try:
        proyectos = obtener_proyectos(nombre)
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")


@app.get("/proyectos/{id}")
async def obtener_proyecto_por_id(id: int):
    """Obtiene un proyecto específico por su ID."""
    proyecto = obtener_proyecto(id)
    if not proyecto:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    return proyecto


@app.post("/proyectos", status_code=201)
async def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto."""
    try:
        nuevo_proyecto = crear_proyecto(proyecto.nombre, proyecto.descripcion)
        return nuevo_proyecto
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear el proyecto: {str(e)}")


@app.put("/proyectos/{id}")
async def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    """Modifica un proyecto existente."""
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    try:
        actualizado = actualizar_proyecto(id, proyecto.nombre, proyecto.descripcion)
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        proyecto_actualizado = obtener_proyecto(id)
        return proyecto_actualizado
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )


@app.delete("/proyectos/{id}")
async def eliminar_proyecto_por_id(id: int):
    """Elimina un proyecto y todas sus tareas asociadas."""
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    resultado = eliminar_proyecto(id)
    if resultado['eliminado']:
        return {
            "mensaje": f"Proyecto {id} eliminado exitosamente",
            "tareas_eliminadas": resultado['tareas_eliminadas']
        }
    else:
        raise HTTPException(status_code=400, detail="Error al eliminar el proyecto")


# ========== ENDPOINTS DE TAREAS ==========

@app.get("/proyectos/{id}/tareas")
async def listar_tareas_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    orden: Literal["asc", "desc"] = "desc"
):
    """Lista todas las tareas de un proyecto específico."""
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    
    tareas = obtener_tareas(proyecto_id=id, estado=estado, prioridad=prioridad, orden=orden)
    return tareas


@app.get("/tareas")
async def listar_todas_tareas(
    proyecto_id: Optional[int] = None,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    orden: Literal["asc", "desc"] = "desc"
):
    """Lista todas las tareas de todos los proyectos con filtros opcionales."""
    try:
        tareas = obtener_tareas(proyecto_id=proyecto_id, estado=estado, prioridad=prioridad, orden=orden)
        return tareas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@app.post("/proyectos/{id}/tareas", status_code=201)
async def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto específico."""
    if not proyecto_existe(id):
        raise HTTPException(status_code=400, detail=f"Proyecto con ID {id} no encontrado")
    
    try:
        nueva_tarea = crear_tarea(
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad,
            id
        )
        return nueva_tarea
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {id} no existe"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al crear la tarea: {str(e)}")


@app.get("/tareas/{id}")
async def obtener_tarea_por_id(id: int):
    """Obtiene una tarea específica por su ID."""
    tarea = obtener_tarea(id)
    if not tarea:
        raise HTTPException(status_code=404, detail=f"Tarea con ID {id} no encontrada")
    return tarea


@app.put("/tareas/{id}")
async def modificar_tarea(id: int, tarea: TareaUpdate):
    """Modifica una tarea existente."""
    tarea_actual = obtener_tarea(id)
    if not tarea_actual:
        raise HTTPException(status_code=404, detail=f"Tarea con ID {id} no encontrada")
    
    # Validar que el nuevo proyecto_id existe si se proporciona
    if tarea.proyecto_id is not None and not proyecto_existe(tarea.proyecto_id):
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {tarea.proyecto_id} no existe"
        )
    
    try:
        actualizado = actualizar_tarea(
            id,
            tarea.descripcion,
            tarea.estado,
            tarea.prioridad,
            tarea.proyecto_id
        )
        if not actualizado:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        tarea_actualizada = obtener_tarea(id)
        return tarea_actualizada
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Error de integridad referencial al actualizar la tarea"
        )


@app.delete("/tareas/{id}")
async def eliminar_tarea_por_id(id: int):
    """Elimina una tarea específica."""
    if not obtener_tarea(id):
        raise HTTPException(status_code=404, detail=f"Tarea con ID {id} no encontrada")
    
    eliminado = eliminar_tarea(id)
    if eliminado:
        return {"mensaje": f"Tarea {id} eliminada exitosamente"}
    else:
        raise HTTPException(status_code=400, detail="Error al eliminar la tarea")


# ========== ENDPOINTS DE RESÚMENES Y ESTADÍSTICAS ==========

@app.get("/proyectos/{id}/resumen")
async def obtener_resumen_de_proyecto(id: int):
    """Obtiene estadísticas detalladas de un proyecto."""
    resumen = obtener_resumen_proyecto(id)
    if not resumen:
        raise HTTPException(status_code=404, detail=f"Proyecto con ID {id} no encontrado")
    return resumen


@app.get("/resumen")
async def obtener_resumen_global():
    """Obtiene estadísticas generales de toda la aplicación."""
    try:
        resumen = obtener_resumen_general()
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


# ========== ENDPOINT RAÍZ ==========

@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas - TP4",
        "version": "1.0.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen",
            "documentacion": "/docs"
        }
    }


# Punto de entrada para ejecutar con uvicorn
if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor en http://localhost:8000")
    print("Documentación disponible en http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)