from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

# Nombre de la base de datos (el test lo usa así)
DB_NAME = "tareas.db"

# ==============================
# Conexión y base de datos
# ==============================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

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
            estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente','en_progreso','completada')),
            prioridad TEXT DEFAULT 'media' CHECK(prioridad IN ('baja','media','alta')),
            fecha_creacion TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ==============================
# Pydantic Models (Actualizado a Pydantic v2)
# ==============================
class ProyectoBase(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class ProyectoCreate(ProyectoBase):
    pass


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class TareaBase(BaseModel):
    descripcion: str
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError("Estado inválido")
        return v

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError("Prioridad inválida")
        return v


class TareaCreate(TareaBase):
    pass


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    proyecto_id: Optional[int] = None


# ==============================
# FastAPI app
# ==============================
app = FastAPI(title="Gestor de Proyectos y Tareas")

# Inicializar DB al arrancar
if not os.path.exists(DB_NAME):
    init_db()


# ==============================
# ENDPOINTS DE PROYECTOS
# ==============================
@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (proyecto.nombre, proyecto.descripcion, datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Nombre de proyecto duplicado")

    proyecto_id = cur.lastrowid
    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    data = dict(cur.fetchone())
    conn.close()
    return data


@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    conn = get_db()
    cur = conn.cursor()

    if nombre:
        cur.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cur.execute("SELECT * FROM proyectos")

    data = [dict(row) for row in cur.fetchall()]
    conn.close()
    return data


@app.get("/proyectos/{proyecto_id}")
def obtener_proyecto(proyecto_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    proyecto = cur.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (proyecto_id,))
    total_tareas = cur.fetchone()[0]
    conn.close()

    data = dict(proyecto)
    data["total_tareas"] = total_tareas
    return data


@app.put("/proyectos/{proyecto_id}")
def actualizar_proyecto(proyecto_id: int, proyecto: ProyectoUpdate):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    campos, valores = [], []
    for campo, valor in proyecto.dict(exclude_unset=True).items():
        campos.append(f"{campo}=?")
        valores.append(valor)
    if campos:
        valores.append(proyecto_id)
        cur.execute(f"UPDATE proyectos SET {', '.join(campos)} WHERE id=?", valores)
        conn.commit()

    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    data = dict(cur.fetchone())
    conn.close()
    return data


@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (proyecto_id,))
    tareas_eliminadas = cur.fetchone()[0]

    cur.execute("DELETE FROM proyectos WHERE id=?", (proyecto_id,))
    conn.commit()

    conn.close()
    return {"tareas_eliminadas": tareas_eliminadas}


# ==============================
# ENDPOINTS DE TAREAS
# ==============================
@app.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM proyectos WHERE id=?", (proyecto_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=400, detail="Proyecto inexistente")

    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion, proyecto_id)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, datetime.now().isoformat(), proyecto_id))
    conn.commit()

    tarea_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,))
    data = dict(cur.fetchone())
    conn.close()
    return data


@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    conn = get_db()
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

    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"

    cur.execute(query, params)
    data = [dict(row) for row in cur.fetchall()]
    conn.close()
    return data


@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_proyecto(proyecto_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM proyectos WHERE id=?", (proyecto_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT * FROM tareas WHERE proyecto_id=?", (proyecto_id,))
    data = [dict(row) for row in cur.fetchall()]
    conn.close()
    return data


@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if tarea.proyecto_id:
        cur.execute("SELECT id FROM proyectos WHERE id=?", (tarea.proyecto_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Proyecto inexistente")

    campos, valores = [], []
    for campo, valor in tarea.dict(exclude_unset=True).items():
        campos.append(f"{campo}=?")
        valores.append(valor)
    if campos:
        valores.append(tarea_id)
        cur.execute(f"UPDATE tareas SET {', '.join(campos)} WHERE id=?", valores)
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,))
    data = dict(cur.fetchone())
    conn.close()
    return data


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM tareas WHERE id=?", (tarea_id,))
    conn.commit()
    conn.close()
    return {"eliminado": True}


# ==============================
# RESÚMENES
# ==============================
@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM proyectos WHERE id=?", (proyecto_id,))
    proyecto = cur.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (proyecto_id,))
    total = cur.fetchone()[0]

    cur.execute("SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id=? GROUP BY estado", (proyecto_id,))
    por_estado = {e: c for e, c in cur.fetchall()}

    cur.execute("SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id=? GROUP BY prioridad", (proyecto_id,))
    por_prioridad = {p: c for p, c in cur.fetchall()}

    conn.close()
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


@app.get("/resumen")
def resumen_general():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cur.fetchone()[0]

    cur.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    tareas_por_estado = {e: c for e, c in cur.fetchall()}

    cur.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad
        FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id ORDER BY cantidad DESC LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        proyecto_con_mas_tareas = {"id": row[0], "nombre": row[1], "cantidad_tareas": row[2]}
    else:
        proyecto_con_mas_tareas = None

    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }
