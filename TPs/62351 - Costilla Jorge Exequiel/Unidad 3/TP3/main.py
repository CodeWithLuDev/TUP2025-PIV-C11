from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="API de Tareas Persistente", version="3.0")

# Nombre de la base de datos
DB_NAME = "tareas.db"

# Modelos Pydantic para validación
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(default="pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

# Función para inicializar la base de datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Inicializar la DB al iniciar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()

# Helper para convertir filas SQL en diccionarios
def row_to_dict(row):
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "fecha_creacion": row[4]
    }

# Endpoints

@app.get("/")
async def root():
    return {
        "nombre": "API de Tareas Persistente",
        "version": "3.0",
        "endpoints": [
            "GET /tareas - Listar todas las tareas",
            "POST /tareas - Crear una tarea",
            "GET /tareas/{id} - Obtener una tarea",
            "PUT /tareas/{id} - Actualizar una tarea",
            "DELETE /tareas/{id} - Eliminar una tarea",
            "GET /tareas/resumen - Resumen de tareas",
            "PUT /tareas/completar_todas - Completar todas las tareas"
        ]
    }

@app.get("/tareas")
async def obtener_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
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
    
    # Ordenamiento por fecha de creación
    if orden in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tareas = [row_to_dict(row) for row in rows]
    return tareas

@app.get("/tareas/resumen")
async def obtener_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Contar total de tareas
    cursor.execute('SELECT COUNT(*) FROM tareas')
    total = cursor.fetchone()[0]
    
    # Resumen por estado
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    ''')
    resultados_estado = cursor.fetchall()
    
    # Resumen por prioridad
    cursor.execute('''
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY prioridad
    ''')
    resultados_prioridad = cursor.fetchall()
    
    conn.close()
    
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for estado, cantidad in resultados_estado:
        por_estado[estado] = cantidad
    
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    for prioridad, cantidad in resultados_prioridad:
        por_prioridad[prioridad] = cantidad
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: TareaCreate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    ''', (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "fecha_creacion": fecha_actual
    }

@app.get("/tareas/{id}")
async def obtener_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="error: Tarea no encontrada")
    
    return row_to_dict(row)

@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
    tarea_actual = cursor.fetchone()
    
    if tarea_actual is None:
        conn.close()
        raise HTTPException(status_code=404, detail="error: Tarea no encontrada")
    
    # Construir la actualización solo con los campos proporcionados
    updates = []
    params = []
    
    if tarea_update.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(tarea_update.descripcion)
    
    if tarea_update.estado is not None:
        updates.append("estado = ?")
        params.append(tarea_update.estado)
    
    if tarea_update.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(tarea_update.prioridad)
    
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    
    return row_to_dict(row)

@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute('SELECT * FROM tareas WHERE id = ?', (id,))
    tarea = cursor.fetchone()
    
    if tarea is None:
        conn.close()
        raise HTTPException(status_code=404, detail="error: Tarea no encontrada")
    
    cursor.execute('DELETE FROM tareas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente"}

@app.put("/tareas/completar_todas")
async def completar_todas_tareas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Se completaron todas las tareas ({filas_afectadas} tareas actualizadas)"
    }