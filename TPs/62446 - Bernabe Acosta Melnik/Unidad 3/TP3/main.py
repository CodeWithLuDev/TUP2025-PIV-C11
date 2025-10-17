from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import sqlite3

app = FastAPI(title="Mini API de Tareas")

# Nombre de la base de datos
DB_NAME = "tareas.db"

# Estados y prioridades válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# ============== MODELOS PYDANTIC ==============

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str
    prioridad: str = "media"

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(default="pendiente")
    prioridad: str = Field(default="media")

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @field_validator("estado")
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        if v not in PRIORIDADES_VALIDAS:
            raise ValueError("Prioridad inválida")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v is not None else v

    @field_validator("estado")
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError("Estado inválido")
        return v

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        if v is not None and v not in PRIORIDADES_VALIDAS:
            raise ValueError("Prioridad inválida")
        return v

# ============== FUNCIONES DE BASE DE DATOS ==============

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
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

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    """Convierte una fila de SQLite en un diccionario"""
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "fecha_creacion": row["fecha_creacion"],
        "prioridad": row["prioridad"]
    }

# Inicializar la base de datos al arrancar
init_db()

# ============== ENDPOINTS ==============

@app.get("/", response_model=dict)
def raiz():
    """Información de la API"""
    return {
        "nombre": "API de Tareas Persistente",
        "version": "3.0",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }

@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir consulta SQL dinámica
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        if estado not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Estado inválido"})
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    if prioridad:
        if prioridad not in PRIORIDADES_VALIDAS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "Prioridad inválida"})
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Ordenamiento
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_dict(row) for row in rows]

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha_actual, tarea.prioridad))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    
    # Obtener la tarea recién creada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row_to_dict(row)

@app.get("/tareas/resumen", response_model=dict)
def resumen_tareas():
    """Devuelve un resumen de tareas por estado y prioridad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    # Resumen por estado
    por_estado = {estado: 0 for estado in ESTADOS_VALIDOS}
    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado")
    for row in cursor.fetchall():
        por_estado[row["estado"]] = row["count"]
    
    # Resumen por prioridad
    por_prioridad = {prioridad: 0 for prioridad in PRIORIDADES_VALIDAS}
    cursor.execute("SELECT prioridad, COUNT(*) as count FROM tareas GROUP BY prioridad")
    for row in cursor.fetchall():
        por_prioridad[row["prioridad"]] = row["count"]
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas", response_model=dict)
def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    cantidad = cursor.rowcount
    conn.commit()
    conn.close()
    
    if cantidad == 0:
        return {"mensaje": "No hay tareas para completar"}
    
    return {"mensaje": f"Se completaron {cantidad} tareas"}

@app.put("/tareas/{tarea_id}", response_model=Tarea)
def actualizar_tarea(tarea_id: int, datos: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Construir actualización dinámica
    updates = []
    params = []
    
    if datos.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(datos.descripcion)
    
    if datos.estado is not None:
        updates.append("estado = ?")
        params.append(datos.estado)
    
    if datos.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(datos.prioridad)
    
    if updates:
        params.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row_to_dict(row)

@app.delete("/tareas/{tarea_id}", response_model=dict)
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}
