from fastapi import FastAPI, HTTPException, Query, status, Body
from pydantic import BaseModel, Field
from datetime import datetime
import sqlite3

app = FastAPI(title="API de Tareas Persistente - TP3")

DB_NAME = "tareas.db"

# ==========================
# CONEXIÓN A BASE DE DATOS
# ==========================
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 200;")
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
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

init_db()

# ==========================
# MODELOS
# ==========================
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field("pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field("media", pattern="^(baja|media|alta)$")

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

# ==========================
# ENDPOINTS CRUD
# ==========================
@app.get("/tareas")
def listar_tareas(
    estado: str | None = None,
    texto: str | None = None,
    prioridad: str | None = None,
    orden: str | None = Query("asc", pattern="^(asc|desc)$")
):
    query = "SELECT * FROM tareas WHERE 1=1"
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

    query += " ORDER BY id DESC" if orden == "desc" else " ORDER BY id ASC"

    conn = get_connection()
    tareas = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(t) for t in tareas]

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaBase):
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía o con solo espacios")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, fecha)
    )
    conn.commit()
    nueva_id = cursor.lastrowid
    conn.close()
    return {
        "id": nueva_id,
        "descripcion": tarea.descripcion.strip(),
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "fecha_creacion": fecha
    }

@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaBase):
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    conn.execute("""
        UPDATE tareas
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, id))
    conn.commit()
    conn.close()
    return {
        "id": id,
        "descripcion": tarea.descripcion.strip(),
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "mensaje": "Tarea actualizada correctamente"
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}

# ==========================
# ENDPOINTS EXTRA
# ==========================
@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_connection()
    cursor_estado = conn.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
    cursor_prioridad = conn.execute("SELECT prioridad, COUNT(*) as cantidad FROM tareas GROUP BY prioridad")
    por_estado = {r["estado"]: r["cantidad"] for r in cursor_estado.fetchall()}
    por_prioridad = {r["prioridad"]: r["cantidad"] for r in cursor_prioridad.fetchall()}
    total = sum(por_estado.values())
    conn.close()
    return {
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
        "total_tareas": total
    }

# 🔹 Endpoint corregido para pasar test y evitar 422
@app.put("/tareas/completar_todas", status_code=200)
def completar_todas_tareas():
    """
    Marca todas las tareas como completadas.
    No requiere body.
    """
    conn = get_connection()
    conn.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}



@app.get("/")
def raiz():
    return {
        "nombre": "API de Tareas Persistente - TP3",
        "autor": "Francisco Javier Castro",
        "version": "1.0",
        "endpoints": [
            "/tareas",
            "/tareas/resumen",
            "/tareas/completar_todas"
        ]
    }
