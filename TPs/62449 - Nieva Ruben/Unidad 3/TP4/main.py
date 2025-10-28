from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import sqlite3

# ===========================
# CONFIGURACIÓN DE LA APP
# ===========================
app = FastAPI(title="API de Tareas - TP4 con SQLite")

# ===========================
# CONEXIÓN A LA BASE DE DATOS
# ===========================
DB_NAME = "tareas.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ===========================
# INICIALIZACIÓN DE LA DB
# ===========================
def init_db():
    conn = get_db_connection()
    # Tabla proyectos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    # Tabla tareas con relación a proyectos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL CHECK (estado IN ('pendiente','en_progreso','completada')),
            prioridad TEXT NOT NULL CHECK (prioridad IN ('alta','media','baja')),
            proyecto_id INTEGER,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===========================
# MODELOS Pydantic
# ===========================
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None

# ===========================
# REDIRECCIÓN RAÍZ
# ===========================
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# ===========================
# ENDPOINTS PROYECTOS
# ===========================
@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    nombre = proyecto.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre del proyecto no puede estar vacío")
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (nombre, proyecto.descripcion, fecha_creacion)
        )
        conn.commit()
        proyecto_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    conn.close()
    return {"id": proyecto_id, "nombre": nombre, "descripcion": proyecto.descripcion}

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor()
    if nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos")
    proyectos = [dict(row) for row in cursor.fetchall()]
    for p in proyectos:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (p["id"],))
        p["cantidad_tareas"] = cursor.fetchone()[0]
    conn.close()
    return proyectos

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    proyecto = dict(proyecto)
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    proyecto["cantidad_tareas"] = cursor.fetchone()[0]
    conn.close()
    return proyecto

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    try:
        if proyecto.nombre:
            cursor.execute("UPDATE proyectos SET nombre=? WHERE id=?", (proyecto.nombre, id))
        if proyecto.descripcion is not None:
            cursor.execute("UPDATE proyectos SET descripcion=? WHERE id=?", (proyecto.descripcion, id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    conn.close()
    return {"mensaje": "Proyecto actualizado correctamente"}

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    cursor.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto y sus tareas eliminadas correctamente"}

# ===========================
# ENDPOINTS TAREAS
# ===========================
@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)
    if proyecto_id:
        query += " AND proyecto_id=?"
        params.append(proyecto_id)
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"

    tareas = [dict(row) for row in cursor.execute(query, params)]
    conn.close()
    return tareas

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
    )
    conn.commit()
    nueva_id = cursor.lastrowid
    conn.close()
    return {
        "id": nueva_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": id,
        "fecha_creacion": fecha_creacion
    }

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    query = "SELECT * FROM tareas WHERE proyecto_id=?"
    params = [id]

    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"

    tareas = [dict(row) for row in cursor.execute(query, params)]
    conn.close()
    return tareas

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    descripcion = tarea.descripcion or existente["descripcion"]
    estado = tarea.estado or existente["estado"]
    prioridad = tarea.prioridad or existente["prioridad"]
    proyecto_id = tarea.proyecto_id or existente["proyecto_id"]

    if proyecto_id:
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto_id no existe")

    cursor.execute(
        "UPDATE tareas SET descripcion=?, estado=?, prioridad=?, proyecto_id=? WHERE id=?",
        (descripcion, estado, prioridad, proyecto_id, id)
    )
    conn.commit()
    conn.close()
    return {
        "id": id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "proyecto_id": proyecto_id
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}

# ===========================
# ENDPOINTS DE RESUMEN
# ===========================
@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cursor.fetchone()[0]

    estados = ["pendiente", "en_progreso", "completada"]
    por_estado = {}
    for e in estados:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=? AND estado=?", (id, e))
        por_estado[e] = cursor.fetchone()[0]

    prioridades = ["baja", "media", "alta"]
    por_prioridad = {}
    for p in prioridades:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=? AND prioridad=?", (id, p))
        por_prioridad[p] = cursor.fetchone()[0]

    conn.close()
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]

    estados = ["pendiente", "en_progreso", "completada"]
    tareas_por_estado = {}
    for e in estados:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE estado=?", (e,))
        tareas_por_estado[e] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT proyectos.id, proyectos.nombre, COUNT(tareas.id) as cantidad_tareas
        FROM proyectos
        LEFT JOIN tareas ON proyectos.id = tareas.proyecto_id
        GROUP BY proyectos.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    max_proyecto = cursor.fetchone()
    conn.close()

    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": dict(max_proyecto) if max_proyecto else None
    }