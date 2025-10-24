from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
import sqlite3
from datetime import datetime
from contextlib import contextmanager

app = FastAPI(title="API de Tareas Persistente", version="1.0.0")

# ========== MODELOS PYDANTIC ==========

class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(default="pendiente")
    prioridad: Literal["baja", "media", "alta"] = Field(default="media")
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

class ResumenTareas(BaseModel):
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

# ========== GESTIÓN DE BASE DE DATOS ==========

DB_NAME = "tareas.db"

@contextmanager
def get_db():
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
    """Inicializa la base de datos creando la tabla si no existe"""
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
        print("✅ Base de datos inicializada correctamente")

# ========== EVENTOS DE LA APLICACIÓN ==========

@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar el servidor"""
    init_db()

# ========== ENDPOINTS ==========

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API de Tareas Persistente",
        "version": "1.0.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "GET /tareas/resumen": "Obtener resumen por estado y prioridad",
            "GET /tareas/{id}": "Obtener una tarea específica",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea existente",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas",
            "DELETE /tareas/{id}": "Eliminar una tarea"
        }
    }

@app.get("/tareas/resumen", response_model=ResumenTareas)
async def obtener_resumen():
    """Devuelve un resumen de tareas agrupadas por estado y prioridad"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
        
        for estado in ["pendiente", "en_progreso", "completada"]:
            por_estado.setdefault(estado, 0)
        
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            GROUP BY prioridad
        """)
        por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
        
        for prioridad in ["baja", "media", "alta"]:
            por_prioridad.setdefault(prioridad, 0)
        
        return {
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/tareas", response_model=list[Tarea])
async def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    texto: Optional[str] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("desc")
):
    """Lista todas las tareas con filtros opcionales"""
    with get_db() as conn:
        cursor = conn.cursor()
        
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
        
        # Ordenar por fecha_creacion directamente (ya incluye microsegundos)
        query += f" ORDER BY fecha_creacion {orden.upper()}"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        return [dict(t) for t in tareas]

# ✅ MOVER ESTE ENDPOINT ANTES DE /tareas/{id}
@app.put("/tareas/completar_todas")
async def completar_todas():
    """Marca todas las tareas como completadas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE estado != 'completada'")
        total = cursor.fetchone()["total"]
        
        cursor.execute("UPDATE tareas SET estado = 'completada'")
        
        return {
            "mensaje": f"Se marcaron {total} tareas como completadas",
            "tareas_actualizadas": total
        }

@app.get("/tareas/{id}", response_model=Tarea)
async def obtener_tarea(id: int):
    """Obtiene una tarea específica por ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(status_code=404, detail=f"error: Tarea con ID {id} no encontrada")
        
        return dict(tarea)

@app.post("/tareas", response_model=Tarea, status_code=201)
async def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Incluir microsegundos para precisión en el ordenamiento
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion))
        
        tarea_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        nueva_tarea = cursor.fetchone()
        
        return dict(nueva_tarea)

@app.put("/tareas/{id}", response_model=Tarea)
async def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """Actualiza una tarea existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail=f"error: Tarea con ID {id} no encontrada")
        
        campos = []
        valores = []
        if tarea_update.descripcion is not None:
            campos.append("descripcion = ?")
            valores.append(tarea_update.descripcion)
        if tarea_update.estado is not None:
            campos.append("estado = ?")
            valores.append(tarea_update.estado)
        if tarea_update.prioridad is not None:
            campos.append("prioridad = ?")
            valores.append(tarea_update.prioridad)
        
        if not campos:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        valores.append(id)
        query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        return dict(cursor.fetchone())

@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    """Elimina una tarea por ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        if not tarea:
            raise HTTPException(status_code=404, detail=f"error: Tarea con ID {id} no encontrada")
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        return {
            "mensaje": "Tarea eliminada exitosamente",
            "id": id,
            "descripcion": tarea["descripcion"]
        }
    