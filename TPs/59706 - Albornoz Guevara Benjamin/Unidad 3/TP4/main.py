from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import time

# Configuración
DB_NAME = "proyectos.db"
app = FastAPI(title="API de Gestión de Proyectos y Tareas")

# ============== MODELOS PYDANTIC ==============

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v or v.strip() == "":
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("El nombre no puede estar vacío")
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = None

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return v.strip() if v else v

class TareaResponse(BaseModel):
    id: int
    proyecto_id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

# ============== BASE DE DATOS ==============

@contextmanager
def get_db():
    """Context manager para conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
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
    """Inicializar la base de datos con las tablas necesarias"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla proyectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        
        # Tabla tareas con clave foránea
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proyecto_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                prioridad TEXT DEFAULT 'media',
                fecha_creacion TEXT NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)

# Inicializar BD al arrancar
init_db()

# ============== ENDPOINTS DE PROYECTOS ==============

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crear un nuevo proyecto"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            fecha_actual = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
                (proyecto.nombre, proyecto.descripcion, fecha_actual)
            )
            proyecto_id = cursor.lastrowid
            
            cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
            row = cursor.fetchone()
            
            return {
                "id": row["id"],
                "nombre": row["nombre"],
                "descripcion": row["descripcion"],
                "fecha_creacion": row["fecha_creacion"]
            }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")

@app.get("/proyectos", response_model=list[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = None):
    """Listar todos los proyectos con filtro opcional por nombre"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if nombre:
            cursor.execute(
                "SELECT * FROM proyectos WHERE nombre LIKE ?",
                (f"%{nombre}%",)
            )
        else:
            cursor.execute("SELECT * FROM proyectos")
        
        proyectos = []
        for row in cursor.fetchall():
            proyectos.append({
                "id": row["id"],
                "nombre": row["nombre"],
                "descripcion": row["descripcion"],
                "fecha_creacion": row["fecha_creacion"]
            })
        
        return proyectos

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int):
    """Obtener un proyecto específico con contador de tareas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Contar tareas
        cursor.execute(
            "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?",
            (proyecto_id,)
        )
        total_tareas = cursor.fetchone()["total"]
        
        return {
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"],
            "fecha_creacion": row["fecha_creacion"],
            "total_tareas": total_tareas
        }

@app.put("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(proyecto_id: int, proyecto: ProyectoUpdate):
    """Actualizar un proyecto existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Actualizar campos proporcionados
        updates = []
        params = []
        
        if proyecto.nombre is not None:
            updates.append("nombre = ?")
            params.append(proyecto.nombre)
        
        if proyecto.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(proyecto.descripcion)
        
        if updates:
            params.append(proyecto_id)
            query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
            try:
                cursor.execute(query, params)
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
        
        # Retornar proyecto actualizado
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "nombre": row["nombre"],
            "descripcion": row["descripcion"],
            "fecha_creacion": row["fecha_creacion"]
        }

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    """Eliminar un proyecto y sus tareas (CASCADE)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Contar tareas antes de eliminar
        cursor.execute(
            "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?",
            (proyecto_id,)
        )
        tareas_eliminadas = cursor.fetchone()["total"]
        
        # Eliminar proyecto (CASCADE eliminará tareas)
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        
        return {
            "mensaje": "Proyecto eliminado exitosamente",
            "tareas_eliminadas": tareas_eliminadas
        }

# ============== ENDPOINTS DE TAREAS ==============

@app.post("/proyectos/{proyecto_id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    """Crear una tarea dentro de un proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="El proyecto no existe")
        
        # Crear tarea con timestamp preciso
        fecha_actual = datetime.now().isoformat()
        # Pequeño delay para asegurar timestamps únicos en tests
        time.sleep(0.001)
        
        cursor.execute(
            """INSERT INTO tareas (proyecto_id, descripcion, estado, prioridad, fecha_creacion) 
               VALUES (?, ?, ?, ?, ?)""",
            (proyecto_id, tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual)
        )
        tarea_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "proyecto_id": row["proyecto_id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "fecha_creacion": row["fecha_creacion"]
        }

@app.get("/proyectos/{proyecto_id}/tareas", response_model=list[TareaResponse])
def listar_tareas_proyecto(proyecto_id: int):
    """Listar todas las tareas de un proyecto específico"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        cursor.execute(
            "SELECT * FROM tareas WHERE proyecto_id = ? ORDER BY fecha_creacion",
            (proyecto_id,)
        )
        
        tareas = []
        for row in cursor.fetchall():
            tareas.append({
                "id": row["id"],
                "proyecto_id": row["proyecto_id"],
                "descripcion": row["descripcion"],
                "estado": row["estado"],
                "prioridad": row["prioridad"],
                "fecha_creacion": row["fecha_creacion"]
            })
        
        return tareas

@app.get("/tareas", response_model=list[TareaResponse])
def listar_todas_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    """Listar todas las tareas con filtros opcionales"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir query con filtros
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado)
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        if proyecto_id:
            query += " AND proyecto_id = ?"
            params.append(proyecto_id)
        
        # Ordenar por fecha - CORRECCIÓN AQUÍ
        if orden == "desc":
            query += " ORDER BY fecha_creacion DESC, id DESC"
        else:
            query += " ORDER BY fecha_creacion ASC, id ASC"
        
        cursor.execute(query, params)
        
        tareas = []
        for row in cursor.fetchall():
            tareas.append({
                "id": row["id"],
                "proyecto_id": row["proyecto_id"],
                "descripcion": row["descripcion"],
                "estado": row["estado"],
                "prioridad": row["prioridad"],
                "fecha_creacion": row["fecha_creacion"]
            })
        
        return tareas

@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    """Actualizar una tarea existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Si se cambia proyecto_id, verificar que existe el nuevo proyecto
        if tarea.proyecto_id is not None:
            cursor.execute("SELECT * FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="El proyecto destino no existe")
        
        # Actualizar campos proporcionados
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
        
        if tarea.proyecto_id is not None:
            updates.append("proyecto_id = ?")
            params.append(tarea.proyecto_id)
        
        if updates:
            params.append(tarea_id)
            query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
        
        # Retornar tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "proyecto_id": row["proyecto_id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "fecha_creacion": row["fecha_creacion"]
        }

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Eliminar una tarea específica"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        
        return {"mensaje": "Tarea eliminada exitosamente"}

# ============== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==============

@app.get("/proyectos/{proyecto_id}/resumen")
def obtener_resumen_proyecto(proyecto_id: int):
    """Obtener resumen estadístico de un proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        proyecto = cursor.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Contar total de tareas
        cursor.execute(
            "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?",
            (proyecto_id,)
        )
        total_tareas = cursor.fetchone()["total"]
        
        # Contar por estado
        cursor.execute(
            """SELECT estado, COUNT(*) as cantidad 
               FROM tareas 
               WHERE proyecto_id = ? 
               GROUP BY estado""",
            (proyecto_id,)
        )
        por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
        
        # Contar por prioridad
        cursor.execute(
            """SELECT prioridad, COUNT(*) as cantidad 
               FROM tareas 
               WHERE proyecto_id = ? 
               GROUP BY prioridad""",
            (proyecto_id,)
        )
        por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
        
        return {
            "proyecto_id": proyecto["id"],
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/resumen")
def obtener_resumen_general():
    """Obtener resumen general de la aplicación"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Contar proyectos
        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()["total"]
        
        # Contar tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Tareas por estado
        cursor.execute(
            "SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado"
        )
        tareas_por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
        
        # Proyecto con más tareas
        cursor.execute(
            """SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
               FROM proyectos p
               LEFT JOIN tareas t ON p.id = t.proyecto_id
               GROUP BY p.id
               ORDER BY cantidad_tareas DESC
               LIMIT 1"""
        )
        proyecto_top = cursor.fetchone()
        
        proyecto_con_mas_tareas = None
        if proyecto_top and proyecto_top["cantidad_tareas"] > 0:
            proyecto_con_mas_tareas = {
                "id": proyecto_top["id"],
                "nombre": proyecto_top["nombre"],
                "cantidad_tareas": proyecto_top["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }

# ============== ENDPOINT RAÍZ ==============

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "API de Gestión de Proyectos y Tareas",
        "version": "1.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen",
            "documentacion": "/docs"
        }
    }