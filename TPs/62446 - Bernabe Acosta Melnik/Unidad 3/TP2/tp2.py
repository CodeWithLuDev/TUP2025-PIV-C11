# main.py - Mini API de Tareas con FastAPI
# Explicaciones detalladas en comentarios línea por línea.

from fastapi import FastAPI, HTTPException, Query, Path
# Importamos FastAPI para crear la aplicación, HTTPException para lanzar errores HTTP
# Query y Path nos ayudan a tipar/validar parámetros de consulta y de ruta.
from pydantic import BaseModel, Field, validator
# Pydantic nos permite definir modelos de datos (esquema) con validaciones.
from typing import List, Optional
# Tipos para anotaciones: List y Optional.
from datetime import datetime, timezone
# Usamos datetime para registrar la fecha de creación con zona horaria UTC.

app = FastAPI()
# Instanciamos la aplicación FastAPI. Esta variable "app" será detectada por Uvicorn/pytest.

# --------------------------------------------------
# Constantes y utilidades
# --------------------------------------------------
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
# Conjunto con los estados aceptados. Usamos un set para comprobaciones O(1).

# --------------------------------------------------
# Modelos de Pydantic (esquemas de entrada/salida)
# --------------------------------------------------
class TareaBase(BaseModel):
    """Modelo base para una tarea: compartido en creación y actualización.

    Los comentarios en los campos explican para qué sirven y sus validaciones.
    """
    descripcion: str = Field(..., title="Descripción", min_length=1)
    # descripcion: campo obligatorio ("..."), con título y longitud mínima 1.
    estado: str = Field("pendiente", title="Estado")
    # estado: por defecto 'pendiente' si no se envía.

    @validator("estado")
    def validar_estado(cls, v):
        # Validamos que el estado pertenezca a ESTADOS_VALIDOS. Si no, lanzamos ValueError
        if v not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido. Valores permitidos: {', '.join(sorted(ESTADOS_VALIDOS))}")
        return v

class Tarea(TareaBase):
    """Modelo completo que representa una tarea almacenada en memoria.

    Incluye el id y la fecha de creación.
    """
    id: int
    creada_en: str
    # Usamos str para serializar la fecha (ISO format). Podríamos usar datetime, pero
    # para compatibilidad con tests y JSON lo exponemos como cadena.

# --------------------------------------------------
# Almacenamiento en memoria
# --------------------------------------------------
_tareas: List[Tarea] = []
# Lista que contiene las tareas almacenadas en memoria.
_proximo_id = 1
# Variable para asignar IDs incrementales.

# --------------------------------------------------
# Funciones auxiliares
# --------------------------------------------------

def _obtener_tarea_index_por_id(tarea_id: int) -> Optional[int]:
    """Devuelve el índice en la lista _tareas de la tarea con id == tarea_id.

    Si no existe devuelve None.
    """
    for index, tarea in enumerate(_tareas):
        if tarea.id == tarea_id:
            return index
    return None


def _ahora_iso() -> str:
    """Devuelve la fecha/hora actual en formato ISO con zona UTC.

    Usamos timezone.utc para dejar claro que es tiempo universal.
    """
    return datetime.now(timezone.utc).isoformat()

# --------------------------------------------------
# Rutas CRUD + funcionalidades adicionales
# --------------------------------------------------

@app.get("/tareas", response_model=List[Tarea])
# Ruta GET /tareas: devuelve una lista de tareas. response_model asegura la serialización.
def listar_tareas(estado: Optional[str] = Query(None, description="Filtrar por estado"),
                  texto: Optional[str] = Query(None, description="Buscar texto en la descripción")):
    """Lista todas las tareas, opcionalmente filtrando por estado y/o por texto en la descripción.

    - estado: si se proporciona, debe ser uno de los ESTADOS_VALIDOS (si no, 400).
    - texto: si se proporciona, se hace búsqueda case-insensitive dentro de la descripcion.
    """
    # Si se proporcionó estado, validamos su valor.
    if estado is not None:
        if estado not in ESTADOS_VALIDOS:
            # Lanzamos HTTPException con código 400 (Bad Request) y mensaje en JSON.
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    resultado = _tareas
    # Filtrado por estado
    if estado is not None:
        resultado = [t for t in resultado if t.estado == estado]

    # Filtrado por texto (caso-insensitive)
    if texto is not None:
        texto_lower = texto.lower()
        resultado = [t for t in resultado if texto_lower in t.descripcion.lower()]

    return resultado
@app.get("/")
def raiz():
    return {"message": "API de Tareas. Usa /tareas para gestionar las tareas."}

@app.post("/tareas", response_model=Tarea, status_code=201)
# POST /tareas: crea una nueva tarea. status_code=201 (Created)
def crear_tarea(tarea_in: TareaBase):
    """Crea una tarea en memoria.

    - Valida que descripción no esté vacía (ya lo hace Pydantic con min_length=1).
    - Valida estado mediante el validador de TareaBase.
    """
    global _proximo_id
    # Generamos la tarea final con id y timestamp.
    tarea = Tarea(
        id=_proximo_id,
        descripcion=tarea_in.descripcion,
        estado=tarea_in.estado,
        creada_en=_ahora_iso()
    )
    _tareas.append(tarea)
    _proximo_id += 1
    return tarea


@app.put("/tareas/{id}", response_model=Tarea)
# PUT /tareas/{id}: actualiza una tarea completa por su id.
def actualizar_tarea(id: int = Path(..., ge=1), tarea_in: TareaBase = None):
    """Actualiza la tarea con id dado.

    - Si no existe: 404.
    - Valida estado y descripcion mediante TareaBase.
    """
    index = _obtener_tarea_index_por_id(id)
    if index is None:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    # Reemplazamos los campos actualizables y preservamos creada_en
    tarea_existente = _tareas[index]
    tarea_actualizada = Tarea(
        id=tarea_existente.id,
        descripcion=tarea_in.descripcion,
        estado=tarea_in.estado,
        creada_en=tarea_existente.creada_en
    )
    _tareas[index] = tarea_actualizada
    return tarea_actualizada


@app.delete("/tareas/{id}", status_code=204)
# DELETE /tareas/{id}: elimina una tarea. status_code=204 (No Content) cuando se borra correctamente.
def eliminar_tarea(id: int = Path(..., ge=1)):
    """Elimina la tarea con id dado.

    - Si no existe: retornamos 404 con mensaje JSON.
    - Si se elimina: retornamos 204 (sin contenido).
    """
    index = _obtener_tarea_index_por_id(id)
    if index is None:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    _tareas.pop(index)
    # FastAPI devolverá 204 automáticamente (sin body) por la decoración.


@app.get("/tareas/resumen")
# GET /tareas/resumen: devuelve el conteo de tareas por estado.
def resumen_tareas():
    """Devuelve un JSON con el conteo de tareas por cada estado válido.

    Si no hay tareas para un estado, su conteo será 0.
    """
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in _tareas:
        resumen[t.estado] += 1
    # Queremos devolver las claves en un orden más legible: pendiente, en_progreso, completada
    orden = ["pendiente", "en_progreso", "completada"]
    return {k: resumen.get(k, 0) for k in orden}


@app.put("/tareas/completar_todas", response_model=List[Tarea])
# PUT /tareas/completar_todas: marca todas las tareas como completadas y devuelve la lista actualizada.
def completar_todas():
    """Marca todas las tareas como 'completada'.

    - Si no hay tareas, simplemente devuelve lista vacía.
    - Retorna las tareas actualizadas.
    """
    for i, tarea in enumerate(_tareas):
        if tarea.estado != "completada":
            # Reemplazamos cada tarea por una nueva instancia con estado cambiado.
            _tareas[i] = Tarea(
                id=tarea.id,
                descripcion=tarea.descripcion,
                estado="completada",
                creada_en=tarea.creada_en
            )
    return _tareas

# --------------------------------------------------
# Nota para ejecutar localmente:
# 1) Instalar dependencias: pip install fastapi uvicorn
# 2) Correr: uvicorn main:app --reload
# 3) La API quedará disponible en http://127.0.0.1:8000
# 4) Documentación automática: http://127.0.0.1:8000/docs
# --------------------------------------------------
