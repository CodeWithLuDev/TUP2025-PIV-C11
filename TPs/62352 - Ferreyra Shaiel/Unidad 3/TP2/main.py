from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enum para los estados válidos de las tareas
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelo para crear una tarea (entrada en POST)
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea, no puede estar vacía")
    estado: EstadoTarea = Field(default=EstadoTarea.pendiente, description="Estado de la tarea")

# Modelo para actualizar una tarea (entrada en PUT)
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1, description="Nueva descripción, si se proporciona")
    estado: Optional[EstadoTarea] = Field(None, description="Nuevo estado, si se proporciona")

# Modelo para la tarea completa (salida en GET)
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    fecha_creacion: datetime

# Inicializamos la app FastAPI
app = FastAPI(title="Mini API de Tareas", description="API para gestionar tareas con FastAPI")

# Almacenamiento en memoria: lista de tareas
tareas: List[Tarea] = []
contador_id = 1  # Para generar IDs autoincrementales

# Ruta raíz opcional para redirigir a /docs (mejora la experiencia)
@app.get("/", include_in_schema=False)
async def read_root():
    return {"message": "Bienvenido a la API de Tareas. Visita /docs para la documentación."}

# Ruta GET /tareas: Obtener todas las tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea], summary="Obtener todas las tareas, con filtros por estado o texto")
async def obtener_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado: pendiente, en_progreso, completada"),
    texto: Optional[str] = Query(None, description="Buscar tareas que contengan este texto en la descripción")
):
    resultado = tareas
    if estado:
        resultado = [tarea for tarea in resultado if tarea.estado == estado]
    if texto:
        resultado = [tarea for tarea in resultado if texto.lower() in tarea.descripcion.lower()]
    return resultado

# Ruta POST /tareas: Crear una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201, summary="Crear una nueva tarea")
async def crear_tarea(tarea_data: TareaCreate):
    global contador_id
    # Validar que después de strip() la descripción no sea vacía
    descripcion_limpia = tarea_data.descripcion.strip()
    if not descripcion_limpia:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede ser solo espacios en blanco"})
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=descripcion_limpia,
        estado=tarea_data.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

# Ruta GET /tareas/resumen: Contar tareas por estado
@app.get("/tareas/resumen", summary="Obtener un resumen de tareas por estado")
async def obtener_resumen():
    resumen = {
        "pendiente": sum(1 for tarea in tareas if tarea.estado == EstadoTarea.pendiente),
        "en_progreso": sum(1 for tarea in tareas if tarea.estado == EstadoTarea.en_progreso),
        "completada": sum(1 for tarea in tareas if tarea.estado == EstadoTarea.completada)
    }
    return resumen

# Ruta PUT /tareas/completar_todas: Marcar todas las tareas como completadas (definida ANTES de /tareas/{id} para evitar conflicto)
@app.put("/tareas/completar_todas", summary="Marcar todas las tareas como completadas")
async def completar_todas():
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for tarea in tareas:
        tarea.estado = EstadoTarea.completada
    return {"mensaje": f"Se completaron {len(tareas)} tareas"}

# Ruta PUT /tareas/{id}: Actualizar una tarea existente (definida DESPUÉS de /tareas/completar_todas)
@app.put("/tareas/{id}", response_model=Tarea, summary="Actualizar una tarea por su ID")
async def actualizar_tarea(id: int, tarea_data: TareaUpdate):
    for tarea in tareas:
        if tarea.id == id:
            if tarea_data.descripcion is not None:
                if not tarea_data.descripcion.strip():
                    raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
                tarea.descripcion = tarea_data.descripcion.strip()
            if tarea_data.estado is not None:
                tarea.estado = tarea_data.estado
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Ruta DELETE /tareas/{id}: Eliminar una tarea
@app.delete("/tareas/{id}", summary="Eliminar una tarea por su ID")
async def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas):
        if tarea.id == id:
            tareas.pop(i)
            return {"mensaje": "Tarea eliminada exitosamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Para desarrollo: ejecutar el servidor si el archivo se corre directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")