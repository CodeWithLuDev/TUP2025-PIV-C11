from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
import os
import atexit
import gc

DB_NAME = "tareas.db"
app = FastAPI(title="TP4 - Relaciones entre Tablas y Filtros Avanzados")

# ============================================
#   INICIALIZACIÓN DE BASE DE DATOS
# ============================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        prioridad TEXT NOT NULL DEFAULT 'media',
        proyecto_id INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()
    gc.collect()  # 🔹 libera el archivo inmediatamente

init_db()

def conexion():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ============================================
#   MODELOS PYDANTIC
# ============================================
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return v.strip()

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    proyecto_id: Optional[int] = None

    @field_validator("descripcion")
    def validar_desc(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

# ============================================
#   CRUD PROYECTOS
# ============================================
@app.post("/proyectos", status_code=201)
def crear_proyecto(data: ProyectoCreate):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE nombre = ?", (data.nombre,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="El proyecto ya existe")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
                (data.nombre, data.descripcion, fecha))
    conn.commit()
    proyecto_id = cur.lastrowid
    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    result = dict(cur.fetchone())
    conn.close()
    gc.collect()
    return result

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = conexion()
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cur.execute("SELECT * FROM proyectos")
    proyectos = [dict(r) for r in cur.fetchall()]
    conn.close()
    gc.collect()
    return proyectos

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cur.fetchone()[0]
    data = dict(proyecto)
    data["total_tareas"] = total_tareas
    conn.close()
    gc.collect()
    return data

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, data: ProyectoCreate):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("UPDATE proyectos SET nombre=?, descripcion=? WHERE id=?",
                (data.nombre, data.descripcion, id))
    conn.commit()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    result = dict(cur.fetchone())
    conn.close()
    gc.collect()
    return result

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    tareas_eliminadas = cur.fetchone()[0]
    cur.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    gc.collect()
    return {"mensaje": "Proyecto eliminado", "tareas_eliminadas": tareas_eliminadas}

# ============================================
#   ENDPOINTS DE TAREAS
# ============================================
@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, data: TareaCreate):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id=?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Proyecto inexistente")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (data.descripcion, data.estado, data.prioridad, id, fecha))
    conn.commit()
    tarea_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,))
    result = dict(cur.fetchone())
    conn.close()
    gc.collect()
    return result

@app.get("/tareas")
def listar_todas_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    conn = conexion()
    cur = conn.cursor()
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

    # ✅ Orden corregido
    if orden == "asc":
        query += " ORDER BY id ASC"
    elif orden == "desc":
        query += " ORDER BY id DESC"
    else:
        query += " ORDER BY id ASC"

    cur.execute(query, tuple(params))
    tareas = [dict(r) for r in cur.fetchall()]
    conn.close()
    gc.collect()
    return tareas

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id=?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT * FROM tareas WHERE proyecto_id=?", (id,))
    tareas = [dict(r) for r in cur.fetchall()]
    conn.close()
    gc.collect()
    return tareas

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, data: dict):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id=?", (id,))
    tarea = cur.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    campos = []
    valores = []
    for key, value in data.items():
        if key == "proyecto_id":
            cur.execute("SELECT id FROM proyectos WHERE id=?", (value,))
            if not cur.fetchone():
                conn.close()
                raise HTTPException(status_code=400, detail="Proyecto inexistente")
        campos.append(f"{key}=?")
        valores.append(value)
    valores.append(id)

    if campos:
        cur.execute(f"UPDATE tareas SET {', '.join(campos)} WHERE id=?", tuple(valores))
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id=?", (id,))
    result = dict(cur.fetchone())
    conn.close()
    gc.collect()
    return result

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    gc.collect()
    return {"mensaje": "Tarea eliminada"}

# ============================================
#   RESUMENES Y ESTADÍSTICAS
# ============================================
@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cur.fetchone()[0]

    estados = ["pendiente", "en_progreso", "completada"]
    prioridades = ["baja", "media", "alta"]
    por_estado = {e: 0 for e in estados}
    por_prioridad = {p: 0 for p in prioridades}

    for e in estados:
        cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=? AND estado=?", (id, e))
        por_estado[e] = cur.fetchone()[0]
    for p in prioridades:
        cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=? AND prioridad=?", (id, p))
        por_prioridad[p] = cur.fetchone()[0]

    conn.close()
    gc.collect()
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = conexion()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cur.fetchone()[0]

    estados = ["pendiente", "en_progreso", "completada"]
    tareas_por_estado = {}
    for e in estados:
        cur.execute("SELECT COUNT(*) FROM tareas WHERE estado=?", (e,))
        tareas_por_estado[e] = cur.fetchone()[0]

    cur.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad
        FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id ORDER BY cantidad DESC LIMIT 1
    """)
    top = cur.fetchone()
    if top:
        proyecto_mas = {"id": top["id"], "nombre": top["nombre"], "cantidad_tareas": top["cantidad"]}
    else:
        proyecto_mas = {"id": None, "nombre": None, "cantidad_tareas": 0}

    conn.close()
    gc.collect()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_mas
    }

# ============================================
#   LIMPIEZA FINAL AUTOMÁTICA
# ============================================
@atexit.register
def cerrar_conexiones():
    gc.collect()
