from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
import os

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
            FOREIGN KEY(proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

# ============================================
#   MODELOS PYDANTIC
# ============================================
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @field_validator("nombre")
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"

    @field_validator("descripcion")
    def validar_desc(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None


# ============================================
#   FUNCIONES AUXILIARES
# ============================================
def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def proyecto_existe(pid: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM proyectos WHERE id=?", (pid,))
    res = cur.fetchone()
    conn.close()
    return bool(res)


# ============================================
#   ENDPOINTS DE PROYECTOS
# ============================================
@app.post("/proyectos", status_code=201)
def crear_proyecto(p: ProyectoCreate):
    conn = conexion()
    cur = conn.cursor()
    try:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        cur.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (p.nombre, p.descripcion, fecha)
        )
        conn.commit()
        pid = cur.lastrowid
        cur.execute("SELECT * FROM proyectos WHERE id=?", (pid,))
        row = cur.fetchone()
        conn.close()
        return {"id": row[0], "nombre": row[1], "descripcion": row[2], "fecha_creacion": row[3]}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")


@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = conexion()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    query = "SELECT * FROM proyectos"
    params = []
    if nombre:
        query += " WHERE nombre LIKE ?"
        params.append(f"%{nombre}%")
    cur.execute(query, params)
    data = cur.fetchall()
    conn.close()
    return data


@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = conexion()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cur.execute("SELECT COUNT(*) AS total FROM tareas WHERE proyecto_id=?", (id,))
    proyecto["total_tareas"] = cur.fetchone()["total"]
    conn.close()
    return proyecto


@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, p: ProyectoUpdate):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    if p.nombre:
        cur.execute("SELECT id FROM proyectos WHERE nombre=? AND id<>?", (p.nombre, id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")

    cur.execute(
        "UPDATE proyectos SET nombre=COALESCE(?, nombre), descripcion=COALESCE(?, descripcion) WHERE id=?",
        (p.nombre, p.descripcion, id)
    )
    conn.commit()
    cur.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "nombre": row[1], "descripcion": row[2], "fecha_creacion": row[3]}


@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    count = cur.fetchone()[0]

    cur.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": "Proyecto eliminado", "tareas_eliminadas": count}


# ============================================
#   ENDPOINTS DE TAREAS
# ============================================
@app.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea(proyecto_id: int, t: TareaCreate):
    if not proyecto_existe(proyecto_id):
        raise HTTPException(status_code=400, detail="El proyecto_id no existe")

    conn = conexion()
    cur = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (t.descripcion, t.estado, t.prioridad, proyecto_id, fecha))
    conn.commit()
    tid = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id=?", (tid,))
    row = cur.fetchone()
    conn.close()
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "proyecto_id": row[4],
        "fecha_creacion": row[5]
    }


@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_proyecto(proyecto_id: int):
    if not proyecto_existe(proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    conn = conexion()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE proyecto_id=?", (proyecto_id,))
    data = cur.fetchall()
    conn.close()
    return data


@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    conn = conexion()
    conn.row_factory = dict_factory
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
    data = cur.fetchall()
    conn.close()
    return data


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, t: TareaUpdate):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    if t.proyecto_id and not proyecto_existe(t.proyecto_id):
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto destino no existe")

    cur.execute("""
        UPDATE tareas
        SET descripcion=COALESCE(?, descripcion),
            estado=COALESCE(?, estado),
            prioridad=COALESCE(?, prioridad),
            proyecto_id=COALESCE(?, proyecto_id)
        WHERE id=?
    """, (t.descripcion, t.estado, t.prioridad, t.proyecto_id, id))
    conn.commit()
    cur.execute("SELECT * FROM tareas WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "proyecto_id": row[4],
        "fecha_creacion": row[5]
    }


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = conexion()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada"}


# ============================================
#   RESÚMENES Y ESTADÍSTICAS
# ============================================
@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    conn = conexion()
    conn.row_factory = dict_factory
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM proyectos WHERE id=?", (id,))
    nombre = cur.fetchone()["nombre"]
    cur.execute("SELECT COUNT(*) AS total FROM tareas WHERE proyecto_id=?", (id,))
    total = cur.fetchone()["total"]

    resumen = {
        "proyecto_id": id,
        "proyecto_nombre": nombre,
        "total_tareas": total,
        "por_estado": {},
        "por_prioridad": {}
    }

    cur.execute("SELECT estado, COUNT(*) c FROM tareas WHERE proyecto_id=? GROUP BY estado", (id,))
    resumen["por_estado"] = {r["estado"]: r["c"] for r in cur.fetchall()}

    cur.execute("SELECT prioridad, COUNT(*) c FROM tareas WHERE proyecto_id=? GROUP BY prioridad", (id,))
    resumen["por_prioridad"] = {r["prioridad"]: r["c"] for r in cur.fetchall()}

    conn.close()
    return resumen


@app.get("/resumen")
def resumen_general():
    conn = conexion()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) total FROM proyectos")
    total_proyectos = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) total FROM tareas")
    total_tareas = cur.fetchone()["total"]
    cur.execute("SELECT estado, COUNT(*) c FROM tareas GROUP BY estado")
    tareas_por_estado = {r["estado"]: r["c"] for r in cur.fetchall()}

    cur.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) AS cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    top = cur.fetchone()
    conn.close()

    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": top or {"id": None, "nombre": None, "cantidad_tareas": 0}
    }


if not os.path.exists(DB_NAME):
    init_db()
