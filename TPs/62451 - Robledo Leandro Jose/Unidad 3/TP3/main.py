import sqlite3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

DB_NAME = "tareas.db"

# Modelos Pydantic para validación
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(default="pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_solo_espacios(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_solo_espacios(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

# Función para inicializar la base de datos
def init_db():
    """Crea la tabla tareas si no existe"""
    conn = sqlite3.connect(DB_NAME)
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
    conn.close()
    print("Base de datos inicializada correctamente")

# Lifespan para gestionar inicio y cierre de la app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar
    init_db()
    print("Servidor iniciado - Base de datos lista")
    yield
    # Código que se ejecuta al cerrar (si fuera necesario)
    print("Servidor detenido")

# Crear la aplicación FastAPI con lifespan
app = FastAPI(
    title="API de Tareas Persistente",
    description="TP3 - Gestión de tareas con SQLite",
    version="1.0.0",
    lifespan=lifespan
)

# Helper para obtener conexión a la BD
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

# Helper para convertir Row a dict
def row_to_dict(row):
    return dict(row) if row else None

@app.get("/")
def read_root():
    return {
        "nombre": "API de Tareas - TP3",
        "version": "1.0.0",
        "endpoints": [
            "GET /tareas - Listar todas las tareas",
            "POST /tareas - Crear una tarea",
            "PUT /tareas/{id} - Actualizar una tarea",
            "DELETE /tareas/{id} - Eliminar una tarea",
            "GET /tareas/resumen - Resumen por estado y prioridad",
            "PUT /tareas/completar_todas - Completar todas las tareas"
        ]
    }

@app.get("/tareas/resumen")
def resumen_tareas():
    """Devuelve un resumen de tareas agrupadas por estado y prioridad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    resultados_estado = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
    resultados_prioridad = cursor.fetchall()
    
    # Contar total
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    conn.close()
    
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    for row in resultados_estado:
        por_estado[row["estado"]] = row["cantidad"]
    
    for row in resultados_prioridad:
        por_prioridad[row["prioridad"]] = row["cantidad"]
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """Marca todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_afectadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Se completaron {filas_afectadas} tareas",
        "tareas_actualizadas": filas_afectadas
    }

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    """
    Lista todas las tareas con filtros opcionales:
    - estado: filtra por estado (pendiente, en_progreso, completada)
    - texto: busca en la descripción
    - prioridad: filtra por prioridad (baja, media, alta)
    - orden: ordena por fecha_creacion (asc o desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir query dinámicamente según filtros
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
    
    # Agregar ordenamiento - CRÍTICO: id también para consistencia
    if orden == "desc":
        query += " ORDER BY id DESC"
    else:
        query += " ORDER BY id ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [row_to_dict(tarea) for tarea in tareas]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea en la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion)
    )
    
    conn.commit()
    tarea_id = cursor.lastrowid
    
    # Obtener la tarea creada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return row_to_dict(nueva_tarea)

@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    """Obtiene una tarea específica por ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    conn.close()
    
    if not tarea:
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    return row_to_dict(tarea)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    # Actualizar solo los campos que se enviaron
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
    
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "No se enviaron campos para actualizar"})
    
    params.append(id)
    query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(query, params)
    conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return row_to_dict(tarea_actualizada)

@app.put("/tareas/completar_todas")
def completar_todas_tareas():
    """Marca todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_afectadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {
        "mensaje": f"Se completaron {filas_afectadas} tareas",
        "tareas_actualizadas": filas_afectadas
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente", "id": id}