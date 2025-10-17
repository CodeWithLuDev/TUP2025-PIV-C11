from fastapi import FastAPI, HTTPException, Query, Body
from typing import Optional, Dict, Any
from datetime import datetime

app = FastAPI(title="Mini API de Tareas", version="1.0.0")

# Estados válidos
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Ruta raíz
@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a la Mini API de Tareas",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea existente",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas por estado",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

# GET /tareas/resumen - DEBE IR ANTES de GET /tareas
@app.get("/tareas/resumen")
def obtener_resumen():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        estado = tarea["estado"]
        if estado in resumen:
            resumen[estado] += 1
    
    return resumen

# PUT /tareas/completar_todas - DEBE IR ANTES de PUT /tareas/{id}
@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    tareas_actualizadas = 0
    for tarea in tareas_db:
        if tarea["estado"] != "completada":
            tarea["estado"] = "completada"
            tareas_actualizadas += 1
    
    return {
        "mensaje": "Todas las tareas han sido marcadas como completadas",
        "tareas_actualizadas": tareas_actualizadas
    }

# GET /tareas - Obtener todas las tareas con filtros opcionales
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None)
):
    resultado = tareas_db.copy()
    
    # Filtrar por estado
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t["estado"] == estado]
    
    # Filtrar por texto en la descripción
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

# POST /tareas - Crear una nueva tarea
@app.post("/tareas", status_code=201)
def crear_tarea(datos: Dict[Any, Any] = Body(...)):
    global contador_id
    
    # Validación manual de descripción
    if "descripcion" not in datos:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "descripcion"],
            "msg": "field required",
            "type": "value_error.missing"
        }])
    
    descripcion = datos.get("descripcion", "")
    
    # Validar que no sea None
    if descripcion is None:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "descripcion"],
            "msg": "La descripción no puede ser nula",
            "type": "value_error"
        }])
    
    # Convertir a string si no lo es
    if not isinstance(descripcion, str):
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "descripcion"],
            "msg": "La descripción debe ser texto",
            "type": "type_error.str"
        }])
    
    # Validar que no esté vacía o solo espacios
    if len(descripcion.strip()) == 0:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "descripcion"],
            "msg": "La descripción no puede estar vacía",
            "type": "value_error"
        }])
    
    # Validar estado
    estado = datos.get("estado", "pendiente")
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail=[{
            "loc": ["body", "estado"],
            "msg": f"Estado debe ser uno de: {', '.join(ESTADOS_VALIDOS)}",
            "type": "value_error"
        }])
    
    nueva_tarea = {
        "id": contador_id,
        "descripcion": descripcion.strip(),
        "estado": estado,
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

# PUT /tareas/{id} - Actualizar una tarea existente
@app.put("/tareas/{id}")
def actualizar_tarea(id: int, datos: Dict[Any, Any] = Body(...)):
    # Buscar la tarea por ID
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Actualizar descripción si se proporciona
    if "descripcion" in datos:
        descripcion = datos["descripcion"]
        if descripcion is not None:
            if not isinstance(descripcion, str):
                raise HTTPException(status_code=422, detail=[{
                    "loc": ["body", "descripcion"],
                    "msg": "La descripción debe ser texto",
                    "type": "type_error.str"
                }])
            if len(descripcion.strip()) == 0:
                raise HTTPException(status_code=422, detail=[{
                    "loc": ["body", "descripcion"],
                    "msg": "La descripción no puede estar vacía",
                    "type": "value_error"
                }])
            tarea["descripcion"] = descripcion.strip()
    
    # Actualizar estado si se proporciona
    if "estado" in datos:
        estado = datos["estado"]
        if estado is not None:
            if estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=422, detail=[{
                    "loc": ["body", "estado"],
                    "msg": f"Estado debe ser uno de: {', '.join(ESTADOS_VALIDOS)}",
                    "type": "value_error"
                }])
            tarea["estado"] = estado
    
    return tarea

# DELETE /tareas/{id} - Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    global tareas_db
    
    # Buscar la tarea por ID
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    tareas_db = [t for t in tareas_db if t["id"] != id]
    
    return {"mensaje": "Tarea eliminada exitosamente"}