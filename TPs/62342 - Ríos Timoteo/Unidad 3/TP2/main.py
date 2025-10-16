from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

app = FastAPI(title="API de Tareas")

# Modelo principal de una tarea
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

# Modelo para crear una tarea
class TareaNueva(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"

# Modelo para editar una tarea
class TareaEditar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

# Base de datos en memoria
tareas_db: List[Tarea] = []
ultimo_id = 1
ESTADOS_PERMITIDOS = {"pendiente", "en_progreso", "completada"}

# Buscar tarea por ID
def encontrar_tarea_por_id(id: int) -> Optional[Tarea]:
    for t in tareas_db:
        if t.id == id:
            return t
    return None

# Redirige la raíz a la documentación
@app.get("/")
def redireccion_inicio():
    return RedirectResponse(url="/docs")

# Listar tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    if estado and estado not in ESTADOS_PERMITIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado no válido"})
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# Crear tarea
@app.post("/tareas", status_code=201, response_model=Tarea)
def crear_tarea(datos: TareaNueva):
    global ultimo_id
    if not datos.descripcion.strip():
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if datos.estado not in ESTADOS_PERMITIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    tarea = Tarea(
        id=ultimo_id,
        descripcion=datos.descripcion.strip(),
        estado=datos.estado.lower(),
        fecha_creacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    tareas_db.append(tarea)
    ultimo_id += 1
    return tarea

# Editar tarea
@app.put("/tareas/{id}", response_model=Tarea)
def editar_tarea(id: int, cambios: TareaEditar):
    tarea = encontrar_tarea_por_id(id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "No se encontró la tarea"})
    if cambios.descripcion is not None:
        if not cambios.descripcion.strip():
            raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
        tarea.descripcion = cambios.descripcion.strip()
    if cambios.estado is not None:
        if cambios.estado not in ESTADOS_PERMITIDOS:
            raise HTTPException(status_code=400, detail={"error": "Estado no permitido"})
        tarea.estado = cambios.estado.lower()
    return tarea

# Eliminar tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    tarea = encontrar_tarea_por_id(id)
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "No existe una tarea con ese ID"})
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada correctamente"}

# Resumen de tareas
@app.get("/tareas/resumen")
def resumen_tareas():
    return {
        "pendiente": sum(t.estado == "pendiente" for t in tareas_db),
        "en_progreso": sum(t.estado == "en_progreso" for t in tareas_db),
        "completada": sum(t.estado == "completada" for t in tareas_db)
    }

# Cambié PUT a POST para evitar 422
@app.post("/tareas/completar_todas", response_model=Dict[str, str])
def completar_todas():
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron completadas"}

