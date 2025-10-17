from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import sqlite3
from datetime import datetime
import os

app = FastAPI()
DB_NAME = "tareas.db"

# ============== MODELOS PYDANTIC ==============

class TareaCreate(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"
    
    @validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()
    
    @validator('estado')
    def estado_valido(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado inválido')
        return v
    
    @validator('prioridad')
    def prioridad_valida(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad inválida')
        return v

class Tarea(TareaCreate):
    id: int
    fecha_creacion: str

# ============== BASE DE DATOS ==============

def init_db():
    """Inicializar la base de datos"""
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

def get_connection():
    """Obtener conexión a la BD"""
    return sqlite3.connect(DB_NAME)

# ============== RUTAS ==============

@app.get("/")
def raiz():
    """Endpoint raíz"""
    return {
        "nombre": "API de Tareas",
        "version": "1.0",
        "endpoints": ["/tareas", "/tareas/resumen", "/tareas/completar_todas"]
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """GET /tareas/resumen - Obtener resumen de tareas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    # Por estado
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas 
        GROUP BY estado
    """)
    por_estado = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas 
        GROUP BY prioridad
    """)
    por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas")
def completar_todas():
    """PUT /tareas/completar_todas - Marcar todas como completadas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tareas 
        SET estado = 'completada'
    """)
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas han sido completadas"}

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = "asc"
):
    """GET /tareas - Obtener tareas con filtros opcionales"""
    conn = get_connection()
    cursor = conn.cursor()
    
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
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": t[0],
            "descripcion": t[1],
            "estado": t[2],
            "fecha_creacion": t[3],
            "prioridad": t[4]
        }
        for t in tareas
    ]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """POST /tareas - Crear una nueva tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha_creacion,
        "prioridad": tarea.prioridad
    }

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: TareaCreate):
    """PUT /tareas/{id} - Actualizar una tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, tarea_id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad
    }

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """DELETE /tareas/{id} - Eliminar una tarea"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}

# ============== INICIALIZACIÓN ==============

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)