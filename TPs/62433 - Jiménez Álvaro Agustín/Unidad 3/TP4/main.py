from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import database as db
from models import (
    ProyectoCreate, ProyectoUpdate, Proyecto,
    TareaCreate, TareaUpdate, Tarea,
    ResumenProyecto, ResumenGeneral
)

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    version="2.0.0",
    description="API para gestionar proyectos y sus tareas con relaciones entre tablas"
)

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def startup_event():
    db.init_db()

# ==================== ENDPOINTS RAÍZ ====================

@app.get("/")
def read_root():
    return {
        "message": "API de Gestión de Proyectos y Tareas",
        "version": "2.0.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "documentacion": "/docs"
        }
    }

# ==================== ENDPOINTS DE PROYECTOS ====================

@app.get("/proyectos", response_model=list[Proyecto])
def listar_proyectos(nombre: Optional[str] = None):
    """Lista todos los proyectos con contador de tareas"""
    proyectos = db.obtener_proyectos(nombre)
    return [
        Proyecto(
            id=p["id"],
            nombre=p["nombre"],
            descripcion=p["descripcion"],
            fecha_creacion=p["fecha_creacion"],
            total_tareas=p["total_tareas"]
        )
        for p in proyectos
    ]

@app.get("/proyectos/{proyecto_id}", response_model=Proyecto)
def obtener_proyecto(proyecto_id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    proyecto = db.obtener_proyecto(proyecto_id)
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "El proyecto no existe"}
        )
    
    return Proyecto(
        id=proyecto["id"],
        nombre=proyecto["nombre"],
        descripcion=proyecto["descripcion"],
        fecha_creacion=proyecto["fecha_creacion"],
        total_tareas=proyecto["total_tareas"]
    )

@app.post("/proyectos", response_model=Proyecto, status_code=status.HTTP_201_CREATED)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    proyecto_id = db.crear_proyecto(proyecto.nombre, proyecto.descripcion)
    
    if proyecto_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"}
        )
    
    nuevo_proyecto = db.obtener_proyecto(proyecto_id)
    return Proyecto(
        id=nuevo_proyecto["id"],
        nombre=nuevo_proyecto["nombre"],
        descripcion=nuevo_proyecto["descripcion"],
        fecha_creacion=nuevo_proyecto["fecha_creacion"],
        total_tareas=nuevo_proyecto["total_tareas"]
    )

@app.put("/proyectos/{proyecto_id}", response_model=Proyecto)
def actualizar_proyecto(proyecto_id: int, proyecto_update: ProyectoUpdate):
    """Modifica un proyecto existente"""
    resultado = db.actualizar_proyecto(
        proyecto_id,
        proyecto_update.nombre,
        proyecto_update.descripcion
    )
    
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "El proyecto no existe"}
        )
    
    if resultado is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Ya existe un proyecto con ese nombre"}
        )
    
    proyecto = db.obtener_proyecto(proyecto_id)
    return Proyecto(
        id=proyecto["id"],
        nombre=proyecto["nombre"],
        descripcion=proyecto["descripcion"],
        fecha_creacion=proyecto["fecha_creacion"],
        total_tareas=proyecto["total_tareas"]
    )

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    """Elimina un proyecto y todas sus tareas asociadas"""
    if not db.eliminar_proyecto(proyecto_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "El proyecto no existe"}
        )
    
    return {"mensaje": "Proyecto eliminado correctamente (incluyendo todas sus tareas)"}

# ==================== ENDPOINTS DE TAREAS ====================

@app.get("/tareas", response_model=list[Tarea])
def listar_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    """Lista todas las tareas con filtros opcionales"""
    tareas = db.obtener_tareas(estado, texto, prioridad, proyecto_id, orden)
    return [
        Tarea(
            id=t["id"],
            descripcion=t["descripcion"],
            estado=t["estado"],
            prioridad=t["prioridad"],
            proyecto_id=t["proyecto_id"],
            proyecto_nombre=t["proyecto_nombre"],
            fecha_creacion=t["fecha_creacion"]
        )
        for t in tareas
    ]

@app.get("/proyectos/{proyecto_id}/tareas", response_model=list[Tarea])
def listar_tareas_de_proyecto(
    proyecto_id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    """Lista todas las tareas de un proyecto específico"""
    tareas = db.obtener_tareas_por_proyecto(proyecto_id, estado, prioridad, orden)
    
    if tareas is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "El proyecto no existe"}
        )
    
    return [
        Tarea(
            id=t["id"],
            descripcion=t["descripcion"],
            estado=t["estado"],
            prioridad=t["prioridad"],
            proyecto_id=t["proyecto_id"],
            proyecto_nombre=t["proyecto_nombre"],
            fecha_creacion=t["fecha_creacion"]
        )
        for t in tareas
    ]

@app.post("/proyectos/{proyecto_id}/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea_en_proyecto(proyecto_id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto"""
    tarea_id = db.crear_tarea(
        tarea.descripcion,
        tarea.estado,
        tarea.prioridad,
        proyecto_id
    )
    
    if tarea_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"El proyecto con ID {proyecto_id} no existe"}
        )
    
    nueva_tarea = db.obtener_tarea(tarea_id)
    return Tarea(
        id=nueva_tarea["id"],
        descripcion=nueva_tarea["descripcion"],
        estado=nueva_tarea["estado"],
        prioridad=nueva_tarea["prioridad"],
        proyecto_id=nueva_tarea["proyecto_id"],
        proyecto_nombre=nueva_tarea["proyecto_nombre"],
        fecha_creacion=nueva_tarea["fecha_creacion"]
    )

@app.get("/tareas/{tarea_id}", response_model=Tarea)
def obtener_tarea(tarea_id: int):
    """Obtiene una tarea específica"""
    tarea = db.obtener_tarea(tarea_id)
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "La tarea no existe"}
        )
    
    return Tarea(
        id=tarea["id"],
        descripcion=tarea["descripcion"],
        estado=tarea["estado"],
        prioridad=tarea["prioridad"],
        proyecto_id=tarea["proyecto_id"],
        proyecto_nombre=tarea["proyecto_nombre"],
        fecha_creacion=tarea["fecha_creacion"]
    )

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int, tarea_update: TareaUpdate):
    """Modifica una tarea existente (puede cambiar de proyecto)"""
    resultado = db.actualizar_tarea(
        tarea_id,
        tarea_update.descripcion,
        tarea_update.estado,
        tarea_update.prioridad,
        tarea_update.proyecto_id
    )
    
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "La tarea no existe"}
        )
    
    if resultado is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "El proyecto especificado no existe"}
        )
    
    tarea = db.obtener_tarea(tarea_id)
    return Tarea(
        id=tarea["id"],
        descripcion=tarea["descripcion"],
        estado=tarea["estado"],
        prioridad=tarea["prioridad"],
        proyecto_id=tarea["proyecto_id"],
        proyecto_nombre=tarea["proyecto_nombre"],
        fecha_creacion=tarea["fecha_creacion"]
    )

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea"""
    if not db.eliminar_tarea(tarea_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "La tarea no existe"}
        )
    
    return {"mensaje": "Tarea eliminada correctamente"}

# ==================== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ====================

@app.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyecto)
def obtener_resumen_proyecto(proyecto_id: int):
    """Devuelve estadísticas detalladas de un proyecto"""
    resumen = db.obtener_resumen_proyecto(proyecto_id)
    
    if resumen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "El proyecto no existe"}
        )
    
    return ResumenProyecto(**resumen)

@app.get("/resumen", response_model=ResumenGeneral)
def obtener_resumen_general():
    """Devuelve estadísticas generales de toda la aplicación"""
    resumen = db.obtener_resumen_general()
    return ResumenGeneral(**resumen)

# ==================== MANEJO DE ERRORES ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )
