from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from contextlib import asynccontextmanager
import sqlite3

# Nombre de la base de datos (para los tests)
DB_NAME = "tareas.db"

# Lifespan event handler (reemplaza on_event startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar
    init_db()
    yield
    # Código que se ejecuta al cerrar (si lo necesitas)

# Crear la aplicación FastAPI
app = FastAPI(title="API de Tareas - TP3", version="1.0.0", lifespan=lifespan)

# Modelos Pydantic con validaciones
class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else None

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

class ResumenTareas(BaseModel):
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

# Función para inicializar la base de datos
def init_db():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL CHECK(estado IN ('pendiente', 'en_progreso', 'completada')) DEFAULT 'pendiente',
        fecha_creacion TEXT DEFAULT (datetime('now', 'localtime')),
        prioridad TEXT NOT NULL CHECK(prioridad IN ('baja', 'media', 'alta')) DEFAULT 'media'
    )
    """)
    
    conexion.commit()
    conexion.close()
    print("✅ Base de datos inicializada correctamente")

# Función auxiliar para obtener conexión
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# 📌 ENDPOINTS

@app.get("/")
async def root():
    return {
        "nombre": "API de Tareas - TP3",
        "version": "1.0.0",
        "mensaje": "API funcionando correctamente",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "GET /tareas/{id}",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar-todas"
        ]
    }

# Obtener resumen de tareas por estado
@app.get("/tareas/resumen", response_model=ResumenTareas)
async def obtener_resumen():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()['total']
    
    # Contar por estado
    cursor.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
    resultados_estado = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("SELECT prioridad, COUNT(*) as cantidad FROM tareas GROUP BY prioridad")
    resultados_prioridad = cursor.fetchall()
    
    conn.close()
    
    # Inicializar contadores de estado
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    # Llenar con los datos obtenidos
    for fila in resultados_estado:
        por_estado[fila['estado']] = fila['cantidad']
    
    # Inicializar contadores de prioridad
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    # Llenar con los datos obtenidos
    for fila in resultados_prioridad:
        por_prioridad[fila['prioridad']] = fila['cantidad']
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

# Completar todas las tareas
@app.put("/tareas/completar_todas")
async def completar_todas_tareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_actualizadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {"mensaje": f"{filas_actualizadas} tareas marcadas como completadas"}

# Obtener todas las tareas con filtros y ordenamiento
@app.get("/tareas")
async def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    texto: Optional[str] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir la consulta SQL dinámicamente
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    # Agregar ordenamiento por fecha_creacion
    if orden == "desc":
        query += " ORDER BY id DESC"  # Ordenar por ID descendente
    else:
        query += " ORDER BY id ASC"   # Ordenar por ID ascendente
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]

# Obtener una tarea por ID
@app.get("/tareas/{tarea_id}", response_model=Tarea)
async def obtener_tarea(tarea_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return dict(tarea)

# Crear una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
async def crear_tarea(tarea: TareaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # NO insertamos fecha_creacion - se genera automáticamente por DEFAULT
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad) VALUES (?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad)
    )
    
    conn.commit()
    tarea_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return dict(nueva_tarea)

# Actualizar una tarea
@app.put("/tareas/{tarea_id}", response_model=Tarea)
async def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if tarea_existente is None:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    # Actualizar solo los campos proporcionados
    if tarea.descripcion is not None:
        cursor.execute(
            "UPDATE tareas SET descripcion = ? WHERE id = ?",
            (tarea.descripcion, tarea_id)
        )
    
    if tarea.estado is not None:
        cursor.execute(
            "UPDATE tareas SET estado = ? WHERE id = ?",
            (tarea.estado, tarea_id)
        )
    
    if tarea.prioridad is not None:
        cursor.execute(
            "UPDATE tareas SET prioridad = ? WHERE id = ?",
            (tarea.prioridad, tarea_id)
        )
    
    conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

# Completar todas las tareas
@app.put("/tareas/completar_todas")
@app.put("/tareas/completar-todas")  # Alias con guión
async def completar_todas_tareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_actualizadas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return {"mensaje": f"{filas_actualizadas} tareas marcadas como completadas"}

# Eliminar una tarea
@app.delete("/tareas/{tarea_id}")
async def eliminar_tarea(tarea_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    
    if tarea is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Tarea {tarea_id} eliminada correctamente"}

# Para ejecutar: uvicorn main:app --reload