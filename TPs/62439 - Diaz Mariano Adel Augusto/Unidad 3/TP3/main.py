from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

# =================== CONFIGURACIÓN DE BASE DE DATOS ===================
DB_NAME = "tareas.db"

def init_db():
    """Crea la base de datos y la tabla tareas si no existen"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Inicializar DB al arrancar
init_db()

# =================== MODELOS PYDANTIC ===================

ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta"]

class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o con solo espacios")
        return v

    @field_validator("estado")
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {ESTADOS_VALIDOS}")
        return v

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        if v not in PRIORIDADES_VALIDAS:
            raise ValueError(f"Prioridad inválida. Debe ser una de: {PRIORIDADES_VALIDAS}")
        return v


class Tarea(TareaBase):
    id: int
    fecha_creacion: str


# =================== CONFIGURACIÓN DE FASTAPI ===================
app = FastAPI(title="API de Tareas Persistente")

# =================== FUNCIONES AUXILIARES ===================

def dict_factory(cursor, row):
    """Convierte una fila en un diccionario"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = dict_factory
    return conn


# =================== ENDPOINTS ===================

@app.get("/")
def raiz():
    """Endpoint raíz: muestra información de la API"""
    return {
        "nombre": "API de Tareas Persistente",
        "endpoints": [
            "/tareas",
            "/tareas/resumen",
            "/tareas/completar_todas"
        ]
    }


# ⚠️ IMPORTANTE: esta ruta debe ir ANTES de /tareas/{id}
@app.put("/tareas/completar_todas")
def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado='completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas fueron completadas"}


@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    """Lista todas las tareas con filtros opcionales"""
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

    # Ordenar por fecha
    query += f" ORDER BY fecha_creacion {orden.upper()}"

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    return tareas


@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaBase):
    """Crea una nueva tarea"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    # Incluimos microsegundos para evitar empates en ordenamiento
    fecha_creacion = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion.strip(), tarea.estado, fecha_creacion, tarea.prioridad))
    conn.commit()

    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    return nueva_tarea


@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaBase):
    """Actualiza una tarea existente"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cursor.fetchone()

    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    cursor.execute("""
        UPDATE tareas SET descripcion=?, estado=?, prioridad=? WHERE id=?
    """, (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, id))
    conn.commit()

    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    actualizada = cursor.fetchone()
    conn.close()
    return actualizada


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea por ID"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    filas = cursor.rowcount
    conn.close()

    if filas == 0:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
def resumen():
    """Devuelve un resumen de tareas por estado y prioridad"""
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total_tareas FROM tareas")
    total = cursor.fetchone()["total_tareas"]

    cursor.execute("SELECT estado, COUNT(*) as c FROM tareas GROUP BY estado")
    por_estado = {fila["estado"]: fila["c"] for fila in cursor.fetchall()}

    cursor.execute("SELECT prioridad, COUNT(*) as c FROM tareas GROUP BY prioridad")
    por_prioridad = {fila["prioridad"]: fila["c"] for fila in cursor.fetchall()}

    conn.close()
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }
