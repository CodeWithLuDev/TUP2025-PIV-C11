# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
import sqlite3
from datetime import datetime
from contextlib import contextmanager

app = FastAPI()
DB_NAME = "tareas.db"

# Modelos Pydantic
class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                proyecto_id INTEGER NOT NULL,
                fecha_creacion TEXT NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

@app.on_event("startup")
def startup():
    init_db()

# ENDPOINTS PROYECTOS
@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    with get_db() as conn:
        if nombre:
            proyectos = conn.execute(
                "SELECT * FROM proyectos WHERE nombre LIKE ?", 
                (f"%{nombre}%",)
            ).fetchall()
        else:
            proyectos = conn.execute("SELECT * FROM proyectos").fetchall()
        return [dict(p) for p in proyectos]

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    with get_db() as conn:
        proyecto = conn.execute("SELECT * FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        cantidad_tareas = conn.execute(
            "SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,)
        ).fetchone()["count"]
        
        result = dict(proyecto)
        result["total_tareas"] = cantidad_tareas
        return result

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    with get_db() as conn:
        existe = conn.execute(
            "SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,)
        ).fetchone()
        if existe:
            raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
        
        fecha_creacion = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (proyecto.nombre, proyecto.descripcion, fecha_creacion)
        )
        conn.commit()
        
        nuevo = conn.execute("SELECT * FROM proyectos WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(nuevo)

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    with get_db() as conn:
        existe = conn.execute("SELECT id FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        if proyecto.nombre:
            duplicado = conn.execute(
                "SELECT id FROM proyectos WHERE nombre = ? AND id != ?", 
                (proyecto.nombre, id)
            ).fetchone()
            if duplicado:
                raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
        
        updates = []
        params = []
        if proyecto.nombre is not None:
            updates.append("nombre = ?")
            params.append(proyecto.nombre)
        if proyecto.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(proyecto.descripcion)
        
        if updates:
            params.append(id)
            conn.execute(
                f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
        
        actualizado = conn.execute("SELECT * FROM proyectos WHERE id = ?", (id,)).fetchone()
        return dict(actualizado)

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    with get_db() as conn:
        existe = conn.execute("SELECT id FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        tareas_eliminadas = conn.execute(
            "SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,)
        ).fetchone()["count"]
        
        conn.execute("DELETE FROM proyectos WHERE id = ?", (id,))
        conn.commit()
        
        return {"tareas_eliminadas": tareas_eliminadas}

# ENDPOINTS TAREAS
@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    orden: Optional[Literal["asc", "desc"]] = None
):
    with get_db() as conn:
        existe = conn.execute("SELECT id FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        query = "SELECT * FROM tareas WHERE proyecto_id = ?"
        params = [id]
        
        if estado:
            query += " AND estado = ?"
            params.append(estado)
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        if orden:
            query += f" ORDER BY fecha_creacion {orden.upper()}"
        
        tareas = conn.execute(query, params).fetchall()
        return [dict(t) for t in tareas]

@app.get("/tareas")
def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[Literal["asc", "desc"]] = None
):
    with get_db() as conn:
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
        
        if orden:
            query += f" ORDER BY fecha_creacion {orden.upper()}"
        
        tareas = conn.execute(query, params).fetchall()
        return [dict(t) for t in tareas]

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    with get_db() as conn:
        existe = conn.execute("SELECT id FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=400, detail="El proyecto especificado no existe")
        
        fecha_creacion = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
            (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
        )
        conn.commit()
        
        nueva = conn.execute("SELECT * FROM tareas WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(nueva)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    with get_db() as conn:
        existe = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        if tarea.proyecto_id:
            proyecto_existe = conn.execute(
                "SELECT id FROM proyectos WHERE id = ?", (tarea.proyecto_id,)
            ).fetchone()
            if not proyecto_existe:
                raise HTTPException(status_code=400, detail="El proyecto especificado no existe")
        
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
            params.append(id)
            conn.execute(
                f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
        
        actualizada = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
        return dict(actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    with get_db() as conn:
        existe = conn.execute("SELECT id FROM tareas WHERE id = ?", (id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminada"}

# ENDPOINTS ESTADÍSTICAS
@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    with get_db() as conn:
        proyecto = conn.execute("SELECT * FROM proyectos WHERE id = ?", (id,)).fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        total = conn.execute(
            "SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,)
        ).fetchone()["count"]
        
        estados = conn.execute(
            "SELECT estado, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY estado",
            (id,)
        ).fetchall()
        
        prioridades = conn.execute(
            "SELECT prioridad, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
            (id,)
        ).fetchall()
        
        por_estado = {e["estado"]: e["count"] for e in estados}
        por_prioridad = {p["prioridad"]: p["count"] for p in prioridades}
        
        return {
            "proyecto_id": proyecto["id"],
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/resumen")
def resumen_general():
    with get_db() as conn:
        total_proyectos = conn.execute("SELECT COUNT(*) as count FROM proyectos").fetchone()["count"]
        total_tareas = conn.execute("SELECT COUNT(*) as count FROM tareas").fetchone()["count"]
        
        estados = conn.execute(
            "SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado"
        ).fetchall()
        
        tareas_por_estado = {e["estado"]: e["count"] for e in estados}
        
        proyecto_max = conn.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """).fetchone()
        
        proyecto_con_mas_tareas = None
        if proyecto_max and proyecto_max["cantidad_tareas"] > 0:
            proyecto_con_mas_tareas = {
                "id": proyecto_max["id"],
                "nombre": proyecto_max["nombre"],
                "cantidad_tareas": proyecto_max["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }