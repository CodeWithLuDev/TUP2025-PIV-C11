import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

DB_NAME = "tareas.db"

app = FastAPI(title="API de Tareas Persistente")

DB_PATH = "tareas.db"
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# Modelos
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field("pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field("media", pattern="^(baja|media|alta)$")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

def tarea_row_to_dict(row):
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "fecha_creacion": row[4]
    }

# GET /tareas (con filtros y orden)
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return JSONResponse(status_code=400, content={"error": "Estado inválido"})
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        if prioridad not in PRIORIDADES_VALIDAS:
            return JSONResponse(status_code=400, content={"error": "Prioridad inválida"})
        query += " AND prioridad = ?"
        params.append(prioridad)
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    if orden not in ("asc", "desc"):
        return JSONResponse(status_code=400, content={"error": "Orden inválido"})
    query += f" ORDER BY fecha_creacion {orden.upper()}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [tarea_row_to_dict(row) for row in rows]

# POST /tareas
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaInput):
    if not tarea.descripcion.strip():
        return JSONResponse(status_code=422, content={"error": "La descripción no puede estar vacía"})
    if tarea.estado not in ESTADOS_VALIDOS:
        return JSONResponse(status_code=400, content={"error": "Estado inválido"})
    if tarea.prioridad not in PRIORIDADES_VALIDAS:
        return JSONResponse(status_code=400, content={"error": "Prioridad inválida"})
    fecha = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, fecha)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    return tarea_row_to_dict(row)

# PUT /tareas/{id}
@app.put("/tareas/{id}", response_model=Tarea)
def modificar_tarea(id: int, tarea: TareaInput):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse(status_code=404, content={"detail": "error: La tarea no existe"})
    if not tarea.descripcion.strip():
        conn.close()
        return JSONResponse(status_code=422, content={"error": "La descripción no puede estar vacía"})
    if tarea.estado not in ESTADOS_VALIDOS:
        return JSONResponse(status_code=422, content={"error": "Estado inválido"})
    if tarea.prioridad not in PRIORIDADES_VALIDAS:
        return JSONResponse(status_code=422, content={"error": "Prioridad inválida"})
    cursor.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ? WHERE id = ?",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return tarea_row_to_dict(row)

# DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse(status_code=404, content={"detail": "error: La tarea no existe"})
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada"}

# GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    por_estado = {estado: 0 for estado in ESTADOS_VALIDOS}
    por_prioridad = {prioridad: 0 for prioridad in PRIORIDADES_VALIDAS}
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    total = 0
    for estado, cantidad in cursor.fetchall():
        por_estado[estado] = cantidad
        total += cantidad
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    for prioridad, cantidad in cursor.fetchall():
        por_prioridad[prioridad] = cantidad
    conn.close()
    return {"por_estado": por_estado, "por_prioridad": por_prioridad, "total_tareas": total}

# GET raíz opcional
@app.get("/")
def root():
    return {
        "nombre": "API de Tareas Persistente",
        "endpoints": ["/tareas", "/tareas/resumen", "/tareas/{id}", "/tareas/completar_todas"],
        "mensaje": "Bienvenido a la API de Tareas Persistente"
    }
# PUT /tareas/completar_todas

@app.put("/tareas/completar_todas")
def completar_todas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas marcadas como completadas"}