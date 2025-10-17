from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
import sqlite3
from datetime import datetime
from typing import Optional

app = FastAPI()
DB_NAME = "tareas.db"

#  MODELOS PYDANTIC 

class TareaBase(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError("El estado debe ser 'pendiente', 'en_progreso' o 'completada'")
        return v

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError("La prioridad debe ser 'baja', 'media' o 'alta'")
        return v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

#  INICIALIZACIÓN DE BASE DE DATOS 

def init_db():
    """Inicializa la base de datos creando la tabla si no existe"""
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

# Inicializar base de datos al arrancar
init_db()

#  ENDPOINTS 

@app.get("/")
def raiz():
    """Endpoint raíz que devuelve información de la API"""
    return {
        "nombre": "API de Tareas Persistente",
        "version": "1.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """PUT /tareas/completar_todas - Marcar todas las tareas como completadas"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

@app.get("/tareas/resumen")
def obtener_resumen():
    """GET /tareas/resumen - Devuelve resumen de tareas por estado y prioridad"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    por_estado = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None, 
                   prioridad: Optional[str] = None, orden: Optional[str] = "asc"):
    """GET /tareas - Obtener tareas con filtros opcionales"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND LOWER(descripcion) LIKE LOWER(?)"
        params.append(f"%{texto}%")
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    resultado = []
    for tarea in tareas:
        resultado.append({
            "id": tarea[0],
            "descripcion": tarea[1],
            "estado": tarea[2],
            "fecha_creacion": tarea[3],
            "prioridad": tarea[4]
        })
    
    return resultado

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaBase):
    """POST /tareas - Crear una nueva tarea"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha_actual, tarea.prioridad))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha_actual,
        "prioridad": tarea.prioridad
    }

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: TareaBase):
    """PUT /tareas/{id} - Actualizar una tarea existente"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("""
        UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, tarea_id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": tarea_existente[3],
        "prioridad": tarea.prioridad
    }

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """DELETE /tareas/{id} - Eliminar una tarea"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}