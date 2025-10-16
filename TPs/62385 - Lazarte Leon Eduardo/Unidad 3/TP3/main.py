from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
from contextlib import contextmanager

# Constante para el nombre de la base de datos
DB_NAME = "tareas.db"

app = FastAPI(title="API de Tareas Persistente", version="3.0")

# Modelos Pydantic para validación
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(default="pendiente")
    prioridad: Literal["baja", "media", "alta"] = Field(default="media")
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip()

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v is not None:
            if not v or v.strip() == "":
                raise ValueError("La descripción no puede estar vacía o contener solo espacios")
            return v.strip()
        return v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

    class Config:
        from_attributes = True

# Gestión de conexión a la base de datos
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Inicialización de la base de datos
def init_db():
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
        conn.commit()
    print("✅ Base de datos inicializada correctamente")

# Inicializar DB al arrancar la aplicación
@app.on_event("startup")
def startup_event():
    init_db()

# Endpoints
@app.get("/")
def root():
    return {
        "mensaje": "API de Tareas Persistente v3.0",
        "endpoints": [
            "GET /tareas - Listar todas las tareas",
            "POST /tareas - Crear una nueva tarea",
            "PUT /tareas/{id} - Actualizar una tarea",
            "DELETE /tareas/{id} - Eliminar una tarea",
            "GET /tareas/resumen - Resumen de tareas por estado"
        ]
    }

@app.get("/tareas", response_model=list[Tarea])
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    texto: Optional[str] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    orden: Optional[str] = Query(None)
):
    """
    Obtiene todas las tareas con filtros opcionales:
    - estado: Filtra por estado de la tarea
    - texto: Busca en la descripción
    - prioridad: Filtra por prioridad
    - orden: Ordena por fecha de creación (asc/desc)
    """
    with get_db() as conn:
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
        
        # Ordenamiento: desc = más reciente primero (orden inverso por ID también)
        if orden and orden.lower() == "desc":
            query += " ORDER BY id DESC"
        else:
            query += " ORDER BY id ASC"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        
        return [dict(tarea) for tarea in tareas]

@app.get("/tareas/resumen")
def resumen_tareas():
    """
    Devuelve un resumen de la cantidad de tareas por estado y prioridad
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Resumen por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM tareas 
            GROUP BY estado
        """)
        por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
        
        # Resumen por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad 
            FROM tareas 
            GROUP BY prioridad
        """)
        por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
        
        # Total
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        return {
            "total_tareas": total,
            "por_estado": {
                "pendiente": por_estado.get("pendiente", 0),
                "en_progreso": por_estado.get("en_progreso", 0),
                "completada": por_estado.get("completada", 0)
            },
            "por_prioridad": {
                "baja": por_prioridad.get("baja", 0),
                "media": por_prioridad.get("media", 0),
                "alta": por_prioridad.get("alta", 0)
            }
        }

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea en la base de datos
    """
    with get_db() as conn:
        cursor = conn.cursor()
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion))
        
        conn.commit()
        tarea_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        nueva_tarea = cursor.fetchone()
        
        return dict(nueva_tarea)

@app.put("/tareas/completar_todas", status_code=200)
def completar_todas_tareas():
    """
    Marca todas las tareas como completadas
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("UPDATE tareas SET estado = 'completada' WHERE estado != 'completada'")
        conn.commit()
        
        filas_afectadas = cursor.rowcount
        
        return {
            "mensaje": "Todas las tareas han sido marcadas como completadas",
            "tareas_actualizadas": filas_afectadas
        }

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_existente = cursor.fetchone()
        
        if not tarea_existente:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        
        # Construir actualización dinámica
        campos_actualizar = []
        valores = []
        
        if tarea_update.descripcion is not None:
            campos_actualizar.append("descripcion = ?")
            valores.append(tarea_update.descripcion)
        
        if tarea_update.estado is not None:
            campos_actualizar.append("estado = ?")
            valores.append(tarea_update.estado)
        
        if tarea_update.prioridad is not None:
            campos_actualizar.append("prioridad = ?")
            valores.append(tarea_update.prioridad)
        
        # Si no hay campos para actualizar, devolver la tarea sin cambios (200 OK)
        if not campos_actualizar:
            return dict(tarea_existente)
        
        valores.append(id)
        query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_actualizada = cursor.fetchone()
        
        return dict(tarea_actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea de la base de datos
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminada exitosamente", "id": id}

# Endpoint adicional: Obtener una tarea específica
@app.get("/tareas/{id}", response_model=Tarea)
def obtener_tarea(id: int):
    """
    Obtiene una tarea específica por su ID
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        
        return dict(tarea)
    