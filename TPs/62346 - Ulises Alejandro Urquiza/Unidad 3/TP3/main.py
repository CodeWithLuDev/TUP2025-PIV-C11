from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sqlite3

app = FastAPI()

# Estados y prioridades válidas
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# Modelo de entrada
class TareaInput(BaseModel):
    description: str = Field(..., min_length=1)
    estado: str = Field(...)
    prioridad: Optional[str] = Field("media")

# Modelo de salida
class Tarea(BaseModel):
    id: int
    description: str
    estado: str
    creada_en: datetime

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# GET /tareas
@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()

    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado = ?"
        params.append(estado)

    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")

    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)

    if orden in ("asc", "desc"):
        query += f" ORDER BY fecha_creacion {orden}"

    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()

    tareas = [
        Tarea(
            id=fila[0],
            description=fila[1],
            estado=fila[2],
            creada_en=datetime.fromisoformat(fila[3])
        )
        for fila in filas
    ]
    return tareas

# POST /tareas
@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaInput):
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    if tarea.prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    fecha_actual = datetime.now().isoformat()

    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.description, tarea.estado, fecha_actual, tarea.prioridad))
    conn.commit()

    nuevo_id = cursor.lastrowid
    conn.close()

    return Tarea(
        id=nuevo_id,
        description=tarea.description,
        estado=tarea.estado,
        creada_en=datetime.fromisoformat(fecha_actual)
    )

# PUT /tareas/{id}
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaInput):
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    if tarea.prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    fila = cursor.fetchone()

    if not fila:
        conn.close()
        raise HTTPException(status_code=404, detail="La tarea no existe")

    cursor.execute("""
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.description, tarea.estado, tarea.prioridad, id))
    conn.commit()
    conn.close()

    return Tarea(
        id=id,
        description=tarea.description,
        estado=tarea.estado,
        creada_en=datetime.fromisoformat(fila[3])
    )

# DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    fila = cursor.fetchone()

    if not fila:
        conn.close()
        raise HTTPException(status_code=404, detail="La tarea no existe")

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": f"Tarea con id {id} eliminada correctamente"}

# GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    conn = sqlite3.connect("tareas.db")
    cursor = conn.cursor()

    resumen = {}
    for estado in ESTADOS_VALIDOS:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE estado = ?", (estado,))
        cantidad = cursor.fetchone()[0]
        resumen[estado] = cantidad

    conn.close()
    return resumen
