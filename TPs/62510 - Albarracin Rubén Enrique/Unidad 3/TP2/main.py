# main.py

# Primero, importo todo lo que necesito de las librerías.
# FastAPI para crear la API, HTTPException para errores, etc.
# Pydantic para los modelos de datos y, muy importante, field_validator para validar campos.
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

# Aquí inicializo mi aplicación FastAPI con un título y una versión.
app = FastAPI(title="Mini API de Tareas", version="1.0.0")

# --- Modelos de Datos (Pydantic) ---

# Este es mi modelo para crear una tarea. Defino los campos que va a tener.
class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(default="pendiente")
    
    # Aquí uso el validador para asegurarme de que la descripción no esté vacía o solo con espacios.
    # Esta es la línea que corregí: cambié @validator por @field_validator.
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

# Este es mi modelo para cuando quiera actualizar una tarea.
# Todos los campos son opcionales, para poder cambiar solo lo que necesite.
class TareaActualizar(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    # También aplico la misma validación aquí para la descripción.
    # Y aquí también corregí el decorador a @field_validator.
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

# --- Base de Datos y Lógica de la Aplicación ---

# Como es un ejemplo, voy a usar una lista en memoria como si fuera mi base de datos.
tareas_db = []
# Y un contador para generar los IDs de las tareas nuevas.
contador_id = 1

# --- Rutas (Endpoints) de la API ---

# Esta es la ruta principal o raíz. Devuelve un simple mensaje de bienvenida.
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}

# Con esta ruta obtengo todas las tareas.
# Le agregué filtros opcionales para buscar por estado o por texto en la descripción.
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Buscar en descripción")
):
    """
    Obtiene todas las tareas, con filtros opcionales por estado o texto.
    """
    # Hago una copia para no modificar la lista original directamente.
    resultado = tareas_db.copy()
    
    # Primero, aplico el filtro por estado si es que me lo pasaron.
    if estado:
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(
                status_code=400,
                detail={"error": "Estado no válido. Debe ser: pendiente, en_progreso o completada"}
            )
        resultado = [t for t in resultado if t["estado"] == estado]
    
    # Después, aplico el filtro por texto si es que me lo pasaron.
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

# Esta ruta es para crear una nueva tarea usando el método POST.
@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    """
    Crea una nueva tarea.
    """
    global contador_id
    
    # Construyo el diccionario de la nueva tarea con los datos que recibí.
    # Le agrego un ID único y la fecha de creación.
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    
    # La agrego a mi "base de datos" y aumento el contador de ID.
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

# Una ruta útil para tener un resumen rápido de cuántas tareas hay en cada estado.
@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Devuelve un contador de tareas por estado.
    """
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    
    return resumen

# Una ruta para marcar todas las tareas como completadas de una sola vez.
@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como completadas.
    """
    tareas_actualizadas = 0
    
    for tarea in tareas_db:
        if tarea["estado"] != "completada":
            tarea["estado"] = "completada"
            tareas_actualizadas += 1
    
    return {
        "mensaje": "Todas las tareas han sido marcadas como completadas",
        "tareas_actualizadas": tareas_actualizadas
    }

# Esta ruta me permite obtener una sola tarea específica usando su ID.
@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    """
    Obtiene una tarea específica por su ID.
    """
    # Busco la tarea en mi lista. Si no la encuentro, devuelvo None.
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    return tarea

# Con esta ruta actualizo una tarea existente usando su ID.
@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: TareaActualizar):
    """
    Actualiza una tarea existente.
    """
    # Primero, busco la tarea que quiero actualizar.
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    # Actualizo solo los campos que me enviaron en el body del request.
    if tarea_actualizada.descripcion is not None:
        tarea["descripcion"] = tarea_actualizada.descripcion
    
    if tarea_actualizada.estado is not None:
        tarea["estado"] = tarea_actualizada.estado
    
    return tarea

# Y finalmente, esta ruta es para eliminar una tarea por su ID.
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea existente.
    """
    global tareas_db
    
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    # Reconstruyo mi lista de tareas, excluyendo la que tiene el ID a eliminar.
    tareas_db = [t for t in tareas_db if t["id"] != id]
    
    return {"mensaje": "Tarea eliminada exitosamente", "tarea": tarea}

# Para ejecutar: uvicorn main:app --reload