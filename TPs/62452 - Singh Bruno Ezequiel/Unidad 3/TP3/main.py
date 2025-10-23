from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import sqlite3
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

DB_NAME = "tareas.db"

# Estados y prioridades válidos
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta"]

def init_db():
    # Creamos la base (archivo) y la tabla con prioridad NOT NULL DEFAULT 'media'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media'
        )
    """)
    conn.commit()
    conn.close()

# Aseguramos que la DB/tabla exista al arrancar (los tests eliminan el archivo antes de llamar a init_db)
init_db()

app = FastAPI()

# Modelo Pydantic actualizado con validaciones
class Tarea(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"

    @validator("estado")
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            # Cambiado ValueError por HTTPException
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        return v

    @validator("prioridad")
    def validar_prioridad(cls, v):
        if v not in PRIORIDADES_VALIDAS:
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})
        return v

# Endpoint raíz: devuelve JSON (el test hace response.json())
from fastapi.responses import HTMLResponse

@app.get("/")
def read_root():
    return {
        "nombre": "API de Tareas",
        "endpoints": ["/tareas", "/tareas/resumen"]
    }


@app.get("/tareas")
def obtener_tareas(estado: str = None, texto: str = None, prioridad: str = None, orden: str = "asc"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
    params = []

    # Filtro por estado
    if estado:
        if estado not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        query += " AND estado = ?"
        params.append(estado)

    # Filtro por texto (case-insensitive)
    if texto:
        query += " AND descripcion LIKE ? COLLATE NOCASE"
        params.append(f"%{texto}%")

    # Filtro por prioridad
    if prioridad:
        if prioridad not in PRIORIDADES_VALIDAS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})
        query += " AND prioridad = ?"
        params.append(prioridad)

    # Orden por fecha_creacion
    if orden.lower() not in ["asc", "desc"]:
        orden = "asc"
    query += f" ORDER BY fecha_creacion {orden.upper()}"

    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()

    tareas = [
        {
            "id": fila[0],
            "descripcion": fila[1],
            "estado": fila[2],
            "fecha_creacion": fila[3],
            "prioridad": fila[4],
        }
        for fila in filas
    ]

    return tareas

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    try:
        descripcion = tarea.descripcion.strip()
        if not descripcion:
            raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})

        estado = tarea.estado
        prioridad = tarea.prioridad
        fecha_creacion = datetime.now().isoformat()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
            VALUES (?, ?, ?, ?)
        """, (descripcion, estado, fecha_creacion, prioridad))
        conn.commit()

        nueva_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (nueva_id,))
        fila = cursor.fetchone()
        conn.close()

        return {
            "id": fila[0],
            "descripcion": fila[1],
            "estado": fila[2],
            "fecha_creacion": fila[3],
            "prioridad": fila[4]
        }

    except ValueError as e:
        # Este bloque evita el error "ValueError is not JSON serializable"
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )


@app.put("/tareas/completar_todas", status_code=200)
def completar_todas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    if total_tareas == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}

    cursor.execute("UPDATE tareas SET estado = ? WHERE estado != ?", ("completada", "completada"))
    conn.commit()

    actualizadas = cursor.rowcount if cursor.rowcount is not None else 0
    conn.close()

    if actualizadas == 0:
        return {"mensaje": "Todas las tareas ya están completadas", "actualizadas": 0}
    else:
        return {"mensaje": "Tareas marcadas como completadas", "actualizadas": actualizadas}

@app.put("/tareas/{id}")
def modificar_tarea(id: int, datos: dict = Body(...)):
    campos_validos = ["descripcion", "estado", "prioridad"]

    if not any(campo in datos for campo in campos_validos):
        raise HTTPException(status_code=422, detail={"error": "No se proporcionaron campos válidos para actualizar"})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        # Mantengo detalle como dict para que el test encuentre response.json()["detail"]["error"]
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    # Validaciones manuales adicionales (aunque Pydantic valida en POST)
    if "descripcion" in datos:
        if not datos["descripcion"].strip():
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})

    if "estado" in datos:
        if datos["estado"] not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})

    if "prioridad" in datos:
        if datos["prioridad"] not in PRIORIDADES_VALIDAS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})

    # Construcción dinámica del UPDATE
    campos = []
    valores = []
    for campo in campos_validos:
        if campo in datos:
            if campo == "descripcion":
                campos.append(f"{campo} = ?")
                valores.append(datos[campo].strip())
            else:
                campos.append(f"{campo} = ?")
                valores.append(datos[campo])

    valores.append(id)
    query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"

    cursor.execute(query, valores)
    conn.commit()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()

    return {
        "id": tarea_actualizada[0],
        "descripcion": tarea_actualizada[1],
        "estado": tarea_actualizada[2],
        "fecha_creacion": tarea_actualizada[3],
        "prioridad": tarea_actualizada[4]
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": f"Tarea con id {id} eliminada exitosamente"}

@app.get("/tareas/resumen")
def resumen_tareas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]

    # Por estado
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    filas_estado = cursor.fetchall()
    por_estado = {estado: 0 for estado in ESTADOS_VALIDOS}
    for estado, cantidad in filas_estado:
        if estado in por_estado:
            por_estado[estado] = cantidad

    # Por prioridad
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    filas_prioridad = cursor.fetchall()
    por_prioridad = {p: 0 for p in PRIORIDADES_VALIDAS}
    for prioridad, cantidad in filas_prioridad:
        if prioridad in por_prioridad:
            por_prioridad[prioridad] = cantidad

    conn.close()

    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

# Manejadores de excepciones (ajustados para los tests)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    # devolvemos el detail tal cual para mantener compatibilidad con tests que esperan response.json()["detail"]
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Error de validación", "detalles": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "detalle": str(exc)}
    )
