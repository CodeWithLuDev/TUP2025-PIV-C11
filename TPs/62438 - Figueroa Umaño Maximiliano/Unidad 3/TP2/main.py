from fastapi import FastAPI, Query, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="Mini API de Tareas - TP2")

# -------------------------
# MODELOS
# -------------------------
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

class TareaCrear(BaseModel):
    descripcion: str
    estado: str = "pendiente"  # Valor por defecto
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v else v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v is not None:
            ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
            if v not in ESTADOS_VALIDOS:
                raise ValueError("Estado inválido")
        return v

# -------------------------
# BASE DE DATOS EN MEMORIA
# -------------------------
tareas_db: List[Tarea] = []
contador_id = 1
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

# -------------------------
# HELPERS
# -------------------------
def validar_estado(valor: str) -> bool:
    return valor in ESTADOS_VALIDOS

# -------------------------
# SANIDAD / HEALTHCHECK
# -------------------------
@app.get("/ping")
def ping():
    return {"ok": True}

# -------------------------
# ENDPOINTS CRUD + EXTRA
# -------------------------
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, description="Filtra por estado válido"),
    texto: Optional[str] = Query(None, description="Filtra por texto contenido en la descripción"),
):
    # Validación de estado (si viene, debe ser válido)
    if estado is not None and not validar_estado(estado):
        raise HTTPException(status_code=400, detail="Estado inválido")

    resultados = tareas_db
    if estado is not None:
        resultados = [t for t in resultados if t.estado == estado]
    if texto:
        resultados = [t for t in resultados if texto.lower() in t.descripcion.lower()]
    return resultados

@app.post("/tareas", status_code=201)
def crear_tarea(payload: TareaCrear):
    global contador_id

    nueva = Tarea(
        id=contador_id,
        descripcion=payload.descripcion,
        estado=payload.estado,
        fecha_creacion=datetime.now(),
    )
    tareas_db.append(nueva)
    contador_id += 1
    return nueva


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas_db:
        if t.estado in resumen:
            resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas(_: Optional[dict] = Body(None)):
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron completadas"}

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, datos: TareaActualizar):
    for t in tareas_db:
        if t.id == id:
            # Actualizaciones
            if datos.descripcion is not None:
                t.descripcion = datos.descripcion
            if datos.estado is not None:
                t.estado = datos.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in list(tareas_db):
        if t.id == id:
            tareas_db.remove(t)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})