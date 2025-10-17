# main.py - TP3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="API de Tareas Persistente")

# -------------------------------
# Configuración de la base de datos
# -------------------------------
DB_NAME = "tareas.db"

@contextmanager
def get_db():
    """Context manager para manejar conexiones a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL
            )
        """)

# Inicializar DB al arrancar
init_db()

# -------------------------------
# 1️⃣ Definir modelo de tarea
# -------------------------------
class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1)
    estado: str
    prioridad: str = "media"
    fecha_creacion: str

# Estados válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# -------------------------------
# 2️⃣ Endpoints
# -------------------------------

# --- GET / --- (Endpoint raíz)
@app.get("/")
def raiz():
    return {
        "mensaje": "API de Tareas Persistente",
        "version": "3.0",
        "endpoints": {
            "tareas": "/tareas",
            "resumen": "/tareas/resumen",
            "completar_todas": "/tareas/completar_todas"
        }
    }

# --- GET /tareas/resumen --- (ANTES de /tareas/{id})
@app.get("/tareas/resumen")
def resumen_tareas():
    with get_db() as conn:
        cursor = conn.cursor()
        por_estado = {estado: 0 for estado in ESTADOS_VALIDOS}
        por_prioridad = {prioridad: 0 for prioridad in PRIORIDADES_VALIDAS}
        total = 0
        
        # Contar por estado
        for estado in ESTADOS_VALIDOS:
            cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE estado = ?", (estado,))
            result = cursor.fetchone()
            count = result[0]
            por_estado[estado] = count
            total += count
        
        # Contar por prioridad
        for prioridad in PRIORIDADES_VALIDAS:
            cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE prioridad = ?", (prioridad,))
            result = cursor.fetchone()
            por_prioridad[prioridad] = result[0]
        
        return {
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

# --- PUT /tareas/completar_todas --- (ANTES de /tareas/{id})
@app.put("/tareas/completar_todas")
def completar_todas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM tareas")
        count = cursor.fetchone()[0]
        
        if count == 0:
            return {"mensaje": "No hay tareas para completar"}
        
        cursor.execute("UPDATE tareas SET estado = 'completada'")
        return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

# --- GET /tareas ---
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir query dinámica
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        # Filtrar por estado
        if estado:
            if estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail="Estado inválido")
            query += " AND estado = ?"
            params.append(estado)
        
        # Filtrar por texto en descripción
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        # Filtrar por prioridad
        if prioridad:
            if prioridad not in PRIORIDADES_VALIDAS:
                raise HTTPException(status_code=400, detail="Prioridad inválida")
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        # Ordenamiento por fecha
        if orden:
            if orden.lower() == "asc":
                query += " ORDER BY fecha_creacion ASC"
            elif orden.lower() == "desc":
                query += " ORDER BY fecha_creacion DESC"
            else:
                raise HTTPException(status_code=400, detail="Orden inválido")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        resultados = []
        for row in rows:
            resultados.append({
                "id": row[0],
                "descripcion": row[1],
                "estado": row[2],
                "prioridad": row[3],
                "fecha_creacion": row[4]
            })
        
        return resultados

# --- POST /tareas ---
class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v and v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v or "pendiente"
    
    @field_validator('prioridad')
    @classmethod
    def validar_prioridad(cls, v):
        if v and v not in PRIORIDADES_VALIDAS:
            raise ValueError('Prioridad inválida')
        return v or "media"

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCrear):
    with get_db() as conn:
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
            (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion)
        )
        
        tarea_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        
        nueva_tarea = {
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "fecha_creacion": row[4]
        }
        
        return nueva_tarea

# --- PUT /tareas/{id} ---
class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v
    
    @field_validator('prioridad')
    @classmethod
    def validar_prioridad(cls, v):
        if v is not None and v not in PRIORIDADES_VALIDAS:
            raise ValueError('Prioridad inválida')
        return v

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaActualizar):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        
        # Construir UPDATE dinámico
        updates = []
        params = []
        
        if tarea.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(tarea.descripcion)
        
        if tarea.estado is not None:
            updates.append("estado = ?")
            params.append(tarea.estado)
        
        if tarea.prioridad is not None:
            updates.append("prioridad = ?")
            params.append(tarea.prioridad)
        
        if updates:
            params.append(id)
            query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
        
        # Obtener tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        tarea_actualizada = {
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "fecha_creacion": row[4]
        }
        
        return tarea_actualizada

# --- DELETE /tareas/{id} ---
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        
        return {"mensaje": "Tarea eliminada correctamente"}