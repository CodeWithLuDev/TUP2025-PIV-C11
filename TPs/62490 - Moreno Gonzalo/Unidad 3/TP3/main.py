from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum
import sqlite3
from contextlib import contextmanager

# Enumeraciones para estados y prioridades válidos
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class PrioridadTarea(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# Modelos Pydantic para validación de datos
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: EstadoTarea = Field(default=EstadoTarea.pendiente, description="Estado de la tarea")
    prioridad: PrioridadTarea = Field(default=PrioridadTarea.media, description="Prioridad de la tarea")
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str

# Configuración de la base de datos
DB_NAME = "tareas.db"

@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
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
    with get_db_connection() as conn:
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
        conn.commit()

# Inicializar FastAPI
app = FastAPI(
    title="API de Tareas con SQLite",
    description="API CRUD persistente para gestión de tareas - TP3",
    version="2.0.0"
)

# Inicializar la base de datos al arrancar
@app.on_event("startup")
def startup_event():
    init_db()

# Función auxiliar para convertir Row en diccionario
def row_to_dict(row):
    """Convierte sqlite3.Row en diccionario"""
    return dict(row) if row else None

# RUTAS DE LA API

@app.get("/")
def root():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "API de Tareas Persistente - TP3",
        "version": "2.0.0",
        "base_datos": "SQLite",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen"
        ]
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Devuelve un contador de tareas por estado y prioridad.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Contar total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Contar por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        estados = cursor.fetchall()
        
        resumen_estados = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        for row in estados:
            resumen_estados[row["estado"]] = row["cantidad"]
        
        # Contar por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            GROUP BY prioridad
        """)
        prioridades = cursor.fetchall()
        
        resumen_prioridades = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        
        for row in prioridades:
            resumen_prioridades[row["prioridad"]] = row["cantidad"]
        
        return {
            "total_tareas": total_tareas,
            "por_estado": resumen_estados,
            "por_prioridad": resumen_prioridades
        }

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """
    Marca todas las tareas como completadas.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si hay tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            return {"mensaje": "No hay tareas"}
        
        # Contar cuántas se van a actualizar
        cursor.execute("""
            SELECT COUNT(*) as cantidad 
            FROM tareas 
            WHERE estado != 'completada'
        """)
        tareas_actualizadas = cursor.fetchone()["cantidad"]
        
        # Actualizar todas a completadas
        cursor.execute("""
            UPDATE tareas 
            SET estado = 'completada' 
            WHERE estado != 'completada'
        """)
        
        return {
            "mensaje": "Todas las tareas han sido marcadas como completadas",
            "tareas_actualizadas": tareas_actualizadas
        }

@app.get("/tareas", response_model=List[TareaResponse])
def listar_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Buscar texto en descripción"),
    prioridad: Optional[PrioridadTarea] = Query(None, description="Filtrar por prioridad"),
    orden: Optional[str] = Query(None, description="Ordenar por fecha: 'asc' o 'desc'")
):
    """
    Lista todas las tareas con filtros opcionales y ordenamiento.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Construir consulta dinámica
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado.value)
        
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad.value)
        
        # Ordenamiento
        if orden and orden.lower() in ['asc', 'desc']:
            query += f" ORDER BY fecha_creacion {orden.upper()}"
        else:
            query += " ORDER BY id ASC"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        
        return [row_to_dict(tarea) for tarea in tareas]

@app.post("/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea en la base de datos.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, fecha_creacion))
        
        tarea_id = cursor.lastrowid
        
        # Obtener la tarea recién creada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        nueva_tarea = cursor.fetchone()
        
        return row_to_dict(nueva_tarea)

@app.put("/tareas/{id}", response_model=TareaResponse)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=404,
                detail={"error": "La tarea no existe"}
            )
        
        # Preparar campos a actualizar
        campos = []
        valores = []
        
        if tarea_update.descripcion is not None:
            campos.append("descripcion = ?")
            valores.append(tarea_update.descripcion)
        
        if tarea_update.estado is not None:
            campos.append("estado = ?")
            valores.append(tarea_update.estado.value)
        
        if tarea_update.prioridad is not None:
            campos.append("prioridad = ?")
            valores.append(tarea_update.prioridad.value)
        
        if campos:
            valores.append(id)
            query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
            cursor.execute(query, valores)
        
        # Obtener la tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_actualizada = cursor.fetchone()
        
        return row_to_dict(tarea_actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea de la base de datos.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=404,
                detail={"error": "La tarea no existe"}
            )
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        
        return {"mensaje": "Tarea eliminada exitosamente"}