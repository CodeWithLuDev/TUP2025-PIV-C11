from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
import os

# ============================================
#   CONFIGURACIÓN INICIAL
# ============================================
DB_NAME = "tareas.db"
app = FastAPI(title="TP3 - API de Tareas Persistente")

# ============================================
#   MODELOS Y VALIDACIONES
# ============================================
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta"]

class TareaBase(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    prioridad: Optional[Literal["baja", "media", "alta"]] = "media"

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

class TareaCrear(TareaBase):
    pass

class TareaActualizar(TareaBase):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

# ============================================
#   BASE DE DATOS
# ============================================
def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT,
            prioridad TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ejecutar al inicio
init_db()

# ============================================
#   ENDPOINT RAÍZ
# ============================================
@app.get("/")
def raiz():
    return {
        "nombre": "API de Tareas Persistente - TP3",
        "endpoints": ["/tareas", "/tareas/resumen", "/tareas/completar_todas"]
    }

# ============================================
#   ENDPOINTS CRUD
# ============================================
@app.post("/tareas", status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCrear):
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail="Estado inválido")
    if tarea.prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=422, detail="Prioridad inválida")

    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha, tarea.prioridad))
    conn.commit()
    tarea_id = cursor.lastrowid

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    fila = cursor.fetchone()
    conn.close()

    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "fecha_creacion": fila[3],
        "prioridad": fila[4],
    }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    conn = get_connection()
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
    if orden:
        query += f" ORDER BY id {orden.upper()}"  # ✅ corregido (orden por ID)

    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()

    return [
        {"id": f[0], "descripcion": f[1], "estado": f[2], "fecha_creacion": f[3], "prioridad": f[4]}
        for f in filas
    ]

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, datos: TareaActualizar):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    existente = cursor.fetchone()

    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    nuevos = {
        "descripcion": datos.descripcion or existente[1],
        "estado": datos.estado or existente[2],
        "prioridad": datos.prioridad or existente[4],
    }

    if nuevos["estado"] not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail="Estado inválido")
    if nuevos["prioridad"] not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=422, detail="Prioridad inválida")

    cursor.execute("""
        UPDATE tareas SET descripcion=?, estado=?, prioridad=? WHERE id=?
    """, (nuevos["descripcion"], nuevos["estado"], nuevos["prioridad"], tarea_id))
    conn.commit()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    fila = cursor.fetchone()
    conn.close()

    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "fecha_creacion": fila[3],
        "prioridad": fila[4],
    }

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}

# ============================================
#   ENDPOINTS ADICIONALES
# ============================================
@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    por_estado = {fila[0]: fila[1] for fila in cursor.fetchall()}

    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    por_prioridad = {fila[0]: fila[1] for fila in cursor.fetchall()}

    conn.close()
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
    }

@app.put("/tareas/completar_todas", status_code=200)  # ✅ corregido
def completar_todas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado='completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
