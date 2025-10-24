from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sqlite3

# ===========================
# CONFIGURACIÓN DE LA APP
# ===========================
app = FastAPI(title="API de Tareas - TP3 con SQLite")

# ===========================
# CONEXIÓN A LA BASE DE DATOS
# ===========================
def get_db_connection():
    conn = sqlite3.connect("tareas.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL CHECK (estado IN ('pendiente','en_progreso','completada')),
            prioridad TEXT NOT NULL CHECK (prioridad IN ('alta','media','baja')),
            fecha_creacion TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()

# ===========================
# MODELOS
# ===========================
class Tarea(BaseModel):
    descripcion: Optional[str] = Field(None, example="Estudiar FastAPI")
    estado: Optional[str] = Field("pendiente", example="pendiente")
    prioridad: Optional[str] = Field("media", example="alta")


# ===========================
# RUTAS
# ===========================
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    estados_validos = ["pendiente", "en_progreso", "completada"]
    prioridades_validas = ["alta", "media", "baja"]

    if estado and estado not in estados_validos:
        conn.close()
        raise HTTPException(status_code=400, detail="Estado inválido")

    if prioridad and prioridad not in prioridades_validas:
        conn.close()
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    query = "SELECT * FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado = ?"
        params.append(estado)

    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)

    if texto:
        query += " AND LOWER(descripcion) LIKE ?"
        params.append(f"%{texto.lower()}%")

    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"

    tareas = [dict(row) for row in cursor.execute(query, params)]
    conn.close()
    return tareas


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    descripcion = (tarea.descripcion or "").strip()
    if not descripcion:
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")

    estado = tarea.estado or "pendiente"
    estados_validos = ["pendiente", "en_progreso", "completada"]
    if estado not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado inválido")

    prioridad = tarea.prioridad or "media"
    prioridades_validas = ["alta", "media", "baja"]
    if prioridad not in prioridades_validas:
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (descripcion, estado, prioridad, fecha_creacion)
    )
    conn.commit()
    nueva_id = cursor.lastrowid
    conn.close()

    return {
        "id": nueva_id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "fecha_creacion": fecha_creacion
    }


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: Tarea):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()

    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    descripcion = (tarea.descripcion or existente["descripcion"]).strip()
    if not descripcion:
        conn.close()
        raise HTTPException(status_code=400, detail="Descripción inválida")

    estado = tarea.estado or existente["estado"]
    estados_validos = ["pendiente", "en_progreso", "completada"]
    if estado not in estados_validos:
        conn.close()
        raise HTTPException(status_code=400, detail="Estado inválido")

    prioridad = tarea.prioridad or existente["prioridad"]
    prioridades_validas = ["alta", "media", "baja"]
    if prioridad not in prioridades_validas:
        conn.close()
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    cursor.execute(
        "UPDATE tareas SET descripcion=?, estado=?, prioridad=? WHERE id=?",
        (descripcion, estado, prioridad, id)
    )
    conn.commit()
    conn.close()

    return {
        "id": id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad
    }


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()

    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    estados = ["pendiente", "en_progreso", "completada"]
    resumen = {}

    for estado in estados:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE estado = ?", (estado,))
        resumen[estado] = cursor.fetchone()[0]

    conn.close()
    return resumen