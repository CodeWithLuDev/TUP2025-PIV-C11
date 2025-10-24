from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import sqlite3

from database import get_connection, init_db, DB_NAME
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoOut,
    TareaCreate, TareaUpdate, TareaOut
)

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

# --- Lifespan (reemplaza @app.on_event('startup')) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    init_db(DB_NAME)
    yield
    # shutdown (n/a)

app = FastAPI(title="TP4 – Proyectos y Tareas", version="1.2.0", lifespan=lifespan)

# --- Helpers ---
def proyecto_exists(conn: sqlite3.Connection, proyecto_id: int) -> bool:
    cur = conn.execute("SELECT 1 FROM proyectos WHERE id = ?", (proyecto_id,))
    return cur.fetchone() is not None

def unique_project_name(conn: sqlite3.Connection, nombre: str, exclude_id: Optional[int] = None) -> bool:
    if exclude_id is None:
        cur = conn.execute("SELECT 1 FROM proyectos WHERE lower(nombre) = lower(?)", (nombre,))
    else:
        cur = conn.execute("SELECT 1 FROM proyectos WHERE lower(nombre) = lower(?) AND id != ?", (nombre, exclude_id))
    return cur.fetchone() is None

# =====================
#   PROYECTOS CRUD
# =====================

@app.get("/proyectos", response_model=List[ProyectoOut])
def listar_proyectos(nombre: Optional[str] = Query(default=None, description="Filtro por nombre que contenga el texto")):
    sql = "SELECT id, nombre, descripcion, fecha_creacion FROM proyectos"
    params = []
    if nombre:
        sql += " WHERE lower(nombre) LIKE ?"
        params.append(f"%{nombre.lower()}%")
    sql += " ORDER BY id ASC"
    with get_connection(DB_NAME) as conn:
        cur = conn.execute(sql, params)
        proyectos = [dict(row) for row in cur.fetchall()]
        for p in proyectos:
            c = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (p["id"],)).fetchone()["c"]
            p["tareas_count"] = c
            p["total_tareas"] = c
        return proyectos

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoOut)
def obtener_proyecto(proyecto_id: int):
    with get_connection(DB_NAME) as conn:
        cur = conn.execute(
            "SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?",
            (proyecto_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        tareas_count = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (proyecto_id,)).fetchone()["c"]
        data = dict(row)
        data["tareas_count"] = tareas_count
        data["total_tareas"] = tareas_count
        return data

@app.post("/proyectos", response_model=ProyectoOut, status_code=201)
def crear_proyecto(payload: ProyectoCreate):
    with get_connection(DB_NAME) as conn:
        if not unique_project_name(conn, payload.nombre):
            raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre.")
        fecha = now_iso()
        cur = conn.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (payload.nombre.strip(), payload.descripcion, fecha),
        )
        proyecto_id = cur.lastrowid
        conn.commit()
        return {
            "id": proyecto_id,
            "nombre": payload.nombre.strip(),
            "descripcion": payload.descripcion,
            "fecha_creacion": fecha,
            "tareas_count": 0,
            "total_tareas": 0,
        }

@app.put("/proyectos/{proyecto_id}", response_model=ProyectoOut)
def actualizar_proyecto(proyecto_id: int, payload: ProyectoUpdate):
    with get_connection(DB_NAME) as conn:
        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        if payload.nombre is not None:
            if not unique_project_name(conn, payload.nombre, exclude_id=proyecto_id):
                raise HTTPException(status_code=409, detail="Ya existe otro proyecto con ese nombre.")
        row = conn.execute("SELECT nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
        nombre = payload.nombre.strip() if payload.nombre is not None else row["nombre"]
        descripcion = payload.descripcion if payload.descripcion is not None else row["descripcion"]
        conn.execute("UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, proyecto_id))
        conn.commit()
        tareas_count = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (proyecto_id,)).fetchone()["c"]
        return {"id": proyecto_id, "nombre": nombre, "descripcion": descripcion, "fecha_creacion": row["fecha_creacion"], "tareas_count": tareas_count, "total_tareas": tareas_count}

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    with get_connection(DB_NAME) as conn:
        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        tcount = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (proyecto_id,)).fetchone()["c"]
        conn.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        conn.commit()
        return {"tareas_eliminadas": tcount}

# =====================
#   TAREAS
# =====================

@app.get("/tareas", response_model=List[TareaOut])
def listar_todas_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = Query(default=None, description="asc|desc por fecha_creacion"),
):
    sql = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas"
    clauses = []
    params = []
    if estado:
        clauses.append("estado = ?")
        params.append(estado)
    if prioridad:
        clauses.append("prioridad = ?")
        params.append(prioridad)
    if proyecto_id is not None:
        clauses.append("proyecto_id = ?")
        params.append(proyecto_id)

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if orden is not None:
        orden_norm = orden.lower()
        if orden_norm not in ("asc", "desc"):
            raise HTTPException(status_code=400, detail="El parámetro 'orden' debe ser 'asc' o 'desc'.")
        sql += f" ORDER BY datetime(fecha_creacion) {orden_norm.upper()}, id {orden_norm.upper()}"
    else:
        sql += " ORDER BY id ASC"

    with get_connection(DB_NAME) as conn:
        if proyecto_id is not None and not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

@app.get("/proyectos/{proyecto_id}/tareas", response_model=List[TareaOut])
def listar_tareas_de_proyecto(proyecto_id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = Query(default=None, description="asc|desc por fecha_creacion"),
):
    with get_connection(DB_NAME) as conn:
        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        sql = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE proyecto_id = ?"
        params = [proyecto_id]
        if estado:
            sql += " AND estado = ?"
            params.append(estado)
        if prioridad:
            sql += " AND prioridad = ?"
            params.append(prioridad)
        if orden is not None:
            orden_norm = orden.lower()
            if orden_norm not in ("asc", "desc"):
                raise HTTPException(status_code=400, detail="El parámetro 'orden' debe ser 'asc' o 'desc'.")
            sql += f" ORDER BY datetime(fecha_creacion) {orden_norm.upper()}, id {orden_norm.upper()}"
        else:
            sql += " ORDER BY id ASC"

        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

@app.post("/proyectos/{proyecto_id}/tareas", response_model=TareaOut, status_code=201)
def crear_tarea_en_proyecto(proyecto_id: int, payload: TareaCreate):
    with get_connection(DB_NAME) as conn:
        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=400, detail="El proyecto_id no existe.")
        fecha = now_iso()
        estado = payload.estado or "pendiente"
        prioridad = payload.prioridad or "media"
        cur = conn.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?,?,?,?,?)",
            (payload.descripcion, estado, prioridad, proyecto_id, fecha),
        )
        tarea_id = cur.lastrowid
        conn.commit()
        return {"id": tarea_id, "descripcion": payload.descripcion, "estado": estado, "prioridad": prioridad, "proyecto_id": proyecto_id, "fecha_creacion": fecha}

@app.put("/tareas/{tarea_id}", response_model=TareaOut)
def actualizar_tarea(tarea_id: int, payload: TareaUpdate):
    with get_connection(DB_NAME) as conn:
        row = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tarea no encontrada.")

        descripcion = payload.descripcion if payload.descripcion is not None else row["descripcion"]
        estado = payload.estado if payload.estado is not None else row["estado"]
        prioridad = payload.prioridad if payload.prioridad is not None else row["prioridad"]
        proyecto_id = payload.proyecto_id if payload.proyecto_id is not None else row["proyecto_id"]

        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=400, detail="El proyecto_id especificado no existe.")

        conn.execute(
            "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ? WHERE id = ?",
            (descripcion, estado, prioridad, proyecto_id, tarea_id),
        )
        conn.commit()
        row = conn.execute("SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
        return dict(row)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    with get_connection(DB_NAME) as conn:
        row = conn.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tarea no encontrada.")
        conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        return {"detail": "Tarea eliminada"}

# =====================
#   RESÚMENES
# =====================

@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    with get_connection(DB_NAME) as conn:
        if not proyecto_exists(conn, proyecto_id):
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        p = conn.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone()
        total = conn.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (proyecto_id,)).fetchone()["c"]

        por_estado = dict(conn.execute(
            "SELECT estado, COUNT(*) c FROM tareas WHERE proyecto_id = ? GROUP BY estado",
            (proyecto_id,)
        ).fetchall())
        por_prioridad = dict(conn.execute(
            "SELECT prioridad, COUNT(*) c FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
            (proyecto_id,)
        ).fetchall())

        for k in ["pendiente", "en_progreso", "completada"]:
            por_estado.setdefault(k, 0)
        for k in ["baja", "media", "alta"]:
            por_prioridad.setdefault(k, 0)

        return {
            "proyecto_id": proyecto_id,
            "proyecto_nombre": p["nombre"],
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad,
        }

@app.get("/resumen")
def resumen_general():
    with get_connection(DB_NAME) as conn:
        total_proyectos = conn.execute("SELECT COUNT(*) c FROM proyectos").fetchone()["c"]
        total_tareas = conn.execute("SELECT COUNT(*) c FROM tareas").fetchone()["c"]

        tareas_por_estado = dict(conn.execute("SELECT estado, COUNT(*) c FROM tareas GROUP BY estado").fetchall())
        for k in ["pendiente", "en_progreso", "completada"]:
            tareas_por_estado.setdefault(k, 0)

        row = conn.execute(
            """
            SELECT p.id, p.nombre, COUNT(t.id) AS cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON t.proyecto_id = p.id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC, p.id ASC
            LIMIT 1
            """
        ).fetchone()

        proyecto_top = None
        if row:
            proyecto_top = {"id": row["id"], "nombre": row["nombre"], "cantidad_tareas": row["cantidad_tareas"]}

        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_top,
        }
