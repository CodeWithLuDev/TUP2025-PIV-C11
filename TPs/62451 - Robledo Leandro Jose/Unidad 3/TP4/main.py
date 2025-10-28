from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
import sqlite3
from datetime import datetime

app = FastAPI()

DB_NAME = 'tareas.db'

# === MODELOS PYDANTIC ===

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

# === FUNCIONES DE BASE DE DATOS ===

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabla proyectos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    # Tabla tareas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# === ENDPOINTS DE PROYECTOS ===

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute(
            "SELECT * FROM proyectos WHERE nombre LIKE ?",
            (f"%{nombre}%",)
        )
    else:
        cursor.execute("SELECT * FROM proyectos")
    
    proyectos = cursor.fetchall()
    conn.close()
    
    return [dict(p) for p in proyectos]

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,))
    count = cursor.fetchone()['count']
    
    conn.close()
    
    resultado = dict(proyecto)
    resultado['total_tareas'] = count
    return resultado

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si existe un proyecto con el mismo nombre
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha_creacion)
    )
    
    proyecto_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    nuevo_proyecto = cursor.fetchone()
    conn.close()
    
    return dict(nuevo_proyecto)

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar nombre duplicado si se está actualizando
    if proyecto.nombre:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (proyecto.nombre, id))
        if cursor.fetchone():
            conn.close()
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
        cursor.execute(
            f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_actualizado = cursor.fetchone()
    conn.close()
    
    return dict(proyecto_actualizado)

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as count FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_eliminadas = cursor.fetchone()['count']
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"tareas_eliminadas": tareas_eliminadas}

# === ENDPOINTS DE TAREAS ===

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
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
        if orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(t) for t in tareas]

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id is not None:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    if orden:
        if orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(t) for t in tareas]

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto especificado no existe")
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
    )
    
    tarea_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return dict(nueva_tarea)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Si se está cambiando el proyecto, verificar que existe
    if tarea.proyecto_id is not None:
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
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
        cursor.execute(
            f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}

# === ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ===

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()['total']
    
    cursor.execute(
        "SELECT estado, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY estado",
        (id,)
    )
    por_estado = {row['estado']: row['count'] for row in cursor.fetchall()}
    
    cursor.execute(
        "SELECT prioridad, COUNT(*) as count FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
        (id,)
    )
    por_prioridad = {row['prioridad']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()['total']
    
    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado")
    tareas_por_estado = {row['estado']: row['count'] for row in cursor.fetchall()}
    
    cursor.execute('''
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    ''')
    proyecto_mas_tareas = cursor.fetchone()
    
    conn.close()
    
    resultado = {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado
    }
    
    if proyecto_mas_tareas and proyecto_mas_tareas['cantidad_tareas'] > 0:
        resultado["proyecto_con_mas_tareas"] = {
            "id": proyecto_mas_tareas['id'],
            "nombre": proyecto_mas_tareas['nombre'],
            "cantidad_tareas": proyecto_mas_tareas['cantidad_tareas']
        }
    
    return resultado