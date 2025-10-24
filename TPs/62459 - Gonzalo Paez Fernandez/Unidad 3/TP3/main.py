from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, constr, field_validator
from contextlib import asynccontextmanager
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
from fastapi.responses import JSONResponse

# Definir el nombre de la base de datos
DB_NAME = "tareas.db"

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inicializar la base de datos
    init_db()
    yield
    # Shutdown: No hay nada que limpiar en este caso

app = FastAPI(lifespan=lifespan)

# Modelos Pydantic para validación de solicitudes/respuestas
class TaskCreate(BaseModel):
    descripcion: constr(min_length=1)
    estado: str = "pendiente"  # Valor por defecto
    prioridad: str = "media"   # Valor por defecto

    @field_validator('descripcion')
    @classmethod
    def validate_descripcion(cls, value):
        # Rechazar descripciones con solo espacios
        if not value.strip():
            raise ValueError("La descripción no puede contener solo espacios")
        return value

    @field_validator('estado')
    @classmethod
    def validate_estado(cls, value):
        valid_states = ["pendiente", "en_progreso", "completada"]
        if value not in valid_states:
            raise ValueError(f"Estado debe ser uno de: {', '.join(valid_states)}")
        return value

    @field_validator('prioridad')
    @classmethod
    def validate_prioridad(cls, value):
        valid_priorities = ["baja", "media", "alta"]
        if value not in valid_priorities:
            raise ValueError(f"Prioridad debe ser una de: {', '.join(valid_priorities)}")
        return value

class TaskResponse(TaskCreate):
    id: int
    fecha_creacion: str

# Inicialización de la base de datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT
        )
    """)
    conn.commit()
    conn.close()

# Función auxiliar para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Endpoint raíz
@app.get("/")
def read_root():
    return {
        "nombre": "API de Tareas Persistente",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "PUT /tareas/completar_todas",
            "GET /tareas/resumen"
        ]
    }

# Endpoints
@app.get("/tareas", response_model=List[TaskResponse])
def get_tasks(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None), prioridad: Optional[str] = Query(None), orden: Optional[str] = Query(None)):
    conn = get_db_connection()
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
    
    # Asegurar ordenamiento correcto
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": task["id"],
            "descripcion": task["descripcion"],
            "estado": task["estado"],
            "prioridad": task["prioridad"],
            "fecha_creacion": task["fecha_creacion"]
        }
        for task in tasks
    ]

@app.post("/tareas", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usar microsegundos para garantizar unicidad en fecha_creacion
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (task.descripcion, task.estado, task.prioridad, fecha_creacion)
    )
    conn.commit()
    
    task_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (task_id,))
    new_task = cursor.fetchone()
    conn.close()
    
    return {
        "id": new_task["id"],
        "descripcion": new_task["descripcion"],
        "estado": new_task["estado"],
        "prioridad": new_task["prioridad"],
        "fecha_creacion": new_task["fecha_creacion"]
    }

@app.put("/tareas/{id}", response_model=TaskResponse)
def update_task(id: int, task: TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existing_task = cursor.fetchone()
    
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ? WHERE id = ?",
        (task.descripcion, task.estado, task.prioridad, id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    updated_task = cursor.fetchone()
    conn.close()
    
    return {
        "id": updated_task["id"],
        "descripcion": updated_task["descripcion"],
        "estado": updated_task["estado"],
        "prioridad": updated_task["prioridad"],
        "fecha_creacion": updated_task["fecha_creacion"]
    }

@app.delete("/tareas/{id}")
def delete_task(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existing_task = cursor.fetchone()
    
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}

@app.put("/tareas/completar_todas", status_code=200)
def complete_all_tasks(_: Optional[Dict] = Body(None)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Actualizar todas las tareas a completada
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.get("/tareas/resumen")
def get_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Resumen por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    summary_estado = cursor.fetchall()
    
    # Resumen por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
    summary_prioridad = cursor.fetchall()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    conn.close()
    
    result = {
        "por_estado": {row["estado"]: row["cantidad"] for row in summary_estado},
        "por_prioridad": {row["prioridad"]: row["cantidad"] for row in summary_prioridad},
        "total_tareas": total_tareas
    }
    return result