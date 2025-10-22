from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, validator
import sqlite3
from datetime import datetime
from fastapi import Body 

DB_NAME = "tareas.db"

app = FastAPI(title="API de Tareas Persistente")

# =========================
# 📦 MODELO Pydantic
# =========================
class TareaInput(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @validator("estado")
    def estado_valido(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError("Estado inválido")
        return v

    @validator("prioridad")
    def prioridad_valida(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError("Prioridad inválida")
        return v

# =========================
# 🗄️ INICIALIZAR BASE DE DATOS
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT,
            prioridad TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# 🔗 ENDPOINTS
# =========================

@app.get("/")
def root():
    return {
        "nombre": "API de Tareas Persistente",
        "endpoints": ["/tareas", "/tareas/resumen", "/tareas/completar_todas"]
    }

@app.get("/tareas")
def obtener_tareas(
    estado: str | None = None,
    texto: str | None = None,
    prioridad: str | None = None,
    orden: str | None = None
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if texto:
        query += " AND LOWER(descripcion) LIKE ?"
        params.append(f"%{texto.lower()}%")
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    if orden in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "descripcion": r[1],
            "estado": r[2],
            "fecha_creacion": r[3],
            "prioridad": r[4]
        }
        for r in rows
    ]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaInput):
    fecha = datetime.now().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, fecha, tarea.prioridad)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()

    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha,
        "prioridad": tarea.prioridad
    }

@app.put("/tareas/completar_todas")
def completar_todas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado='completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaInput):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    cursor.execute("""
        UPDATE tareas SET descripcion=?, estado=?, prioridad=?
        WHERE id=?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id))
    conn.commit()
    conn.close()
    return {"id": id, **tarea.dict()}

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
def resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    por_estado = {estado: count for estado, count in cursor.fetchall()}

    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    por_prioridad = {p: c for p, c in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]

    conn.close()
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

# Compatibilidad con TestClient de los tests sin modificar los tests
def get_app():
    return app