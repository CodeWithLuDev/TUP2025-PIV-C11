from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="TP2 - Mini API de Tareas")

# MODELOS
class TareaIn(BaseModel):
    descripcion: str = Field(..., example="Estudiar para el parcial")
    estado: Optional[str] = Field("pendiente", example="pendiente")

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @validator("estado")
    def estado_valido(cls, v):
        estados_validos = {"pendiente", "en_progreso", "completada"}
        if v not in estados_validos:
            raise ValueError("Estado inválido")
        return v

class Tarea(TareaIn):
    id: int
    fecha_creacion: str

#DB EN MEMORIA
tareas: List[dict] = []
contador_id = 1
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

#HELPERS
def buscar_tarea_por_id(id: int):
    for t in tareas:
        if t["id"] == id:
            return t
    return None

#ENDPOINTS

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    """
    Lista todas las tareas. Opcionalmente filtra por estado y/o texto en la descripción.
    Ejemplos:
      /tareas?estado=pendiente
      /tareas?texto=pan
    """
    resultado = tareas
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    return resultado


@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea_in: TareaIn):
    """
    Crea una nueva tarea. descripcion obligatorio; estado opcional (por defecto 'pendiente').
    Valida descripcion no vacía y estado válido.
    """
    global contador_id
    tarea = {
        "id": contador_id,
        "descripcion": tarea_in.descripcion,
        "estado": tarea_in.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas.append(tarea)
    contador_id += 1
    return tarea


@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, datos: TareaIn):
    """
    Actualiza descripción y/o estado de la tarea con id.
    Devuelve 404 si no existe; 400 si validaciones fallan.
    """
    t = buscar_tarea_por_id(id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "La tarea no existe"})
    # Validaciones 
    t["descripcion"] = datos.descripcion
    t["estado"] = datos.estado
    return t


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina la tarea por id. Si no existe, retorna 404.
    """
    t = buscar_tarea_por_id(id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "La tarea no existe"})
    tareas.remove(t)
    return {"mensaje": "Tarea eliminada"}


@app.get("/tareas/resumen")
def resumen():
    """
    Devuelve conteo de tareas por estado.
    """
    conteo = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas:
        conteo[t["estado"]] += 1
    return conteo


@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como completadas.
    Si no hay tareas, devuelve mensaje informativo (los tests esperan comportamiento correcto).
    """
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas:
        t["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron completadas"}

