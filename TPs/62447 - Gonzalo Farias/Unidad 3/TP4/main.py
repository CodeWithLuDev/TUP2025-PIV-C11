# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, field_validator

import sqlite3

from database import init_db, get_connection
from database import init_db, get_connection, DB_PATH

from models import (
    # Proyectos
    ProyectoCreate, ProyectoUpdate, ProyectoOut, ProyectoDetalleOut,
    # Tareas
    TareaCreate, TareaUpdate, TareaOut,
    # Resúmenes
    ResumenProyectoOut, ResumenGlobalOut,
)

app = FastAPI(title="TP4 - Proyectos y Tareas", version="1.0.0")

DB_NAME = str(DB_PATH)  # ruta completa a tareas.db para que el test la use


EstadoLiteral = Literal["pendiente", "en_progreso", "completada"]
PrioridadLiteral = Literal["baja", "media", "alta"]

class TareaCreate(BaseModel):
    descripcion: str
    estado: EstadoLiteral = "pendiente"    # DEFAULT
    prioridad: PrioridadLiteral = "media"  # DEFAULT

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if v is None or v.strip() == "":
            raise ValueError("La descripción de la tarea no puede estar vacía.")
        return v.strip()
    
# -------------------- Startup --------------------
@app.on_event("startup")
def on_startup():
    init_db()  # crea tablas si no existen


# -------------------- Utils --------------------
def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}

def proyecto_exists(proyecto_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    exists = cur.execute("SELECT 1 FROM proyectos WHERE id = ?", (proyecto_id,)).fetchone() is not None
    conn.close()
    return exists

VALID_ESTADOS = {"pendiente", "en_progreso", "completada"}
VALID_PRIORIDADES = {"baja", "media", "alta"}

def validar_orden(orden: Optional[str]) -> str:
    if orden and orden.lower() in ("asc", "desc"):
        return orden.lower()
    return "desc"

def filtros_tareas_where(
    estado: Optional[str],
    prioridad: Optional[str],
    proyecto_id: Optional[int]
):
    conditions = []
    params = []

    if estado:
        if estado not in VALID_ESTADOS:
            raise HTTPException(status_code=400, detail="El estado debe ser uno de: pendiente, en_progreso, completada.")
        conditions.append("estado = ?")
        params.append(estado)

    if prioridad:
        if prioridad not in VALID_PRIORIDADES:
            raise HTTPException(status_code=400, detail="La prioridad debe ser una de: baja, media, alta.")
        conditions.append("prioridad = ?")
        params.append(prioridad)

    if proyecto_id is not None:
        conditions.append("proyecto_id = ?")
        params.append(proyecto_id)

    where = ""
    if conditions:
        where = " WHERE " + " AND ".join(conditions)
    return where, params


# ==================== PROYECTOS ====================

@app.get("/proyectos", response_model=List[ProyectoOut])
def listar_proyectos(nombre: Optional[str] = Query(default=None, description="Filtro contiene por nombre")):
    conn = get_connection()
    cur = conn.cursor()

    if nombre:
        rows = cur.execute(
            "SELECT id, nombre, descripcion, fecha_creacion "
            "FROM proyectos WHERE nombre LIKE ? ORDER BY fecha_creacion DESC",
            (f"%{nombre}%",),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, nombre, descripcion, fecha_creacion "
            "FROM proyectos ORDER BY fecha_creacion DESC"
        ).fetchall()

    conn.close()
    return [ProyectoOut(**row_to_dict(r)) for r in rows]


@app.get("/proyectos/{id}", response_model=ProyectoDetalleOut)
def obtener_proyecto(id: int):
    conn = get_connection()
    cur = conn.cursor()

    proy = cur.execute(
        "SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?",
        (id,),
    ).fetchone()
    if not proy:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    total = cur.execute(
        "SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?",
        (id,),
    ).fetchone()["c"]

    conn.close()
    data = row_to_dict(proy)
    data["total_tareas"] = total
    return ProyectoDetalleOut(**data)


@app.post("/proyectos", response_model=ProyectoOut, status_code=201)
def crear_proyecto(payload: ProyectoCreate):
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_connection()
    cur = conn.cursor()

    dup = cur.execute("SELECT 1 FROM proyectos WHERE nombre = ?", (payload.nombre,)).fetchone()
    if dup:
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre.")

    try:
        cur.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (payload.nombre, payload.descripcion, now),
        )
        conn.commit()
        new_id = cur.lastrowid
    finally:
        conn.close()

    return ProyectoOut(id=new_id, nombre=payload.nombre, descripcion=payload.descripcion, fecha_creacion=now)




@app.put("/proyectos/{id}", response_model=ProyectoOut)
def actualizar_proyecto(id: int, payload: ProyectoUpdate):
    conn = get_connection()
    cur = conn.cursor()

    actual = cur.execute(
        "SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?",
        (id,),
    ).fetchone()
    if not actual:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    data = dict(actual)
    nuevo_nombre = payload.nombre if payload.nombre is not None else data["nombre"]
    nueva_desc  = payload.descripcion if payload.descripcion is not None else data["descripcion"]

    if nuevo_nombre != data["nombre"]:
        dup = cur.execute(
            "SELECT 1 FROM proyectos WHERE nombre = ? AND id <> ?",
            (nuevo_nombre, id),
        ).fetchone()
        if dup:
            conn.close()
            raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre.")

    cur.execute(
        "UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?",
        (nuevo_nombre, nueva_desc, id),
    )
    conn.commit()
    conn.close()

    return ProyectoOut(id=id, nombre=nuevo_nombre, descripcion=nueva_desc, fecha_creacion=data["fecha_creacion"])


@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    """
    Elimina un proyecto. ON DELETE CASCADE se encarga de sus tareas.
    Devuelve 200 con la cantidad de tareas eliminadas.
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1) Verificar existencia
    existe = cur.execute("SELECT 1 FROM proyectos WHERE id = ?", (id,)).fetchone()
    if not existe:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    # 2) Contar tareas asociadas ANTES del borrado
    cant_tareas = cur.execute(
        "SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?",
        (id,)
    ).fetchone()["c"]

    # 3) Borrar proyecto (las tareas se borran por CASCADE)
    cur.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    # 4) Respuesta que el test espera
    return {
        "detail": "Proyecto eliminado",
        "tareas_eliminadas": cant_tareas
    }



# ==================== TAREAS ====================

@app.get("/tareas", response_model=List[TareaOut])
def listar_todas_las_tareas(
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    proyecto_id: Optional[int] = Query(default=None),
    orden: Optional[str] = Query(default=None, description="asc|desc por fecha_creacion"),
):
    order = validar_orden(orden)
    where, params = filtros_tareas_where(estado, prioridad, proyecto_id)

    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
    "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion "
    f"FROM tareas{where} ORDER BY fecha_creacion {order}, id {order}",
    params
    ).fetchall()
    conn.close()
    return [TareaOut(**row_to_dict(r)) for r in rows]


@app.get("/proyectos/{id}/tareas", response_model=List[TareaOut])
def listar_tareas_de_proyecto(
    id: int,
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default=None),
):
    if not proyecto_exists(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    order = validar_orden(orden)
    where, params = filtros_tareas_where(estado, prioridad, None)

    # forzar proyecto_id
    if where:
        where = where + " AND proyecto_id = ?"
    else:
        where = " WHERE proyecto_id = ?"
    params.append(id)

    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
    "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion "
    f"FROM tareas{where} ORDER BY fecha_creacion {order}, id {order}",
    params
    ).fetchall()
    conn.close()
    return [TareaOut(**row_to_dict(r)) for r in rows]


@app.post("/proyectos/{id}/tareas", response_model=TareaOut, status_code=201)
def crear_tarea_en_proyecto(id: int, payload: TareaCreate):
    # ✅ El test espera 400 si el proyecto no existe
    conn = get_connection()
    cur = conn.cursor()

    existe = cur.execute("SELECT 1 FROM proyectos WHERE id = ?", (id,)).fetchone()
    if not existe:
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto_id indicado no existe.")

    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) "
        "VALUES (?, ?, ?, ?, ?)",
        (payload.descripcion, payload.estado, payload.prioridad, id, now)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return TareaOut(
        id=new_id,
        descripcion=payload.descripcion,
        estado=payload.estado,
        prioridad=payload.prioridad,
        proyecto_id=id,
        fecha_creacion=now
    )



@app.put("/tareas/{id}", response_model=TareaOut)
def actualizar_tarea(id: int, payload: TareaUpdate):
    conn = get_connection()
    cur = conn.cursor()

    actual = cur.execute(
        "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE id = ?",
        (id,)
    ).fetchone()
    if not actual:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    data = dict(actual)
    nueva_desc = payload.descripcion if payload.descripcion is not None else data["descripcion"]
    nuevo_estado = payload.estado if payload.estado is not None else data["estado"]
    nueva_prioridad = payload.prioridad if payload.prioridad is not None else data["prioridad"]
    nuevo_proyecto_id = payload.proyecto_id if payload.proyecto_id is not None else data["proyecto_id"]

    # Validaciones de dominio
    if nuevo_estado not in VALID_ESTADOS:
        conn.close()
        raise HTTPException(status_code=400, detail="El estado debe ser uno de: pendiente, en_progreso, completada.")
    if nueva_prioridad not in VALID_PRIORIDADES:
        conn.close()
        raise HTTPException(status_code=400, detail="La prioridad debe ser una de: baja, media, alta.")
    if not proyecto_exists(nuevo_proyecto_id):
        conn.close()
        raise HTTPException(status_code=404, detail="El proyecto_id indicado no existe.")

    cur.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ? WHERE id = ?",
        (nueva_desc, nuevo_estado, nueva_prioridad, nuevo_proyecto_id, id)
    )
    conn.commit()
    conn.close()

    return TareaOut(
        id=id,
        descripcion=nueva_desc,
        estado=nuevo_estado,
        prioridad=nueva_prioridad,
        proyecto_id=nuevo_proyecto_id,
        fecha_creacion=data["fecha_creacion"]
    )


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_connection()
    cur = conn.cursor()

    existe = cur.execute("SELECT 1 FROM tareas WHERE id = ?", (id,)).fetchone()
    if not existe:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    cur.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    # 200 OK con mensaje (el test solo verifica el status)
    return {"detail": "Tarea eliminada"}


# ==================== RESÚMENES ====================

@app.get("/proyectos/{id}/resumen", response_model=ResumenProyectoOut)
def resumen_proyecto(id: int):
    conn = get_connection()
    cur = conn.cursor()

    proy = cur.execute("SELECT id, nombre FROM proyectos WHERE id = ?", (id,)).fetchone()
    if not proy:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    total = cur.execute("SELECT COUNT(*) AS c FROM tareas WHERE proyecto_id = ?", (id,)).fetchone()["c"]

    # por estado
    por_estado_rows = cur.execute(
        "SELECT estado, COUNT(*) AS c FROM tareas WHERE proyecto_id = ? GROUP BY estado", (id,)
    ).fetchall()
    por_estado: Dict[str, int] = {r["estado"]: r["c"] for r in por_estado_rows}
    for e in VALID_ESTADOS:
        por_estado.setdefault(e, 0)

    # por prioridad
    por_prioridad_rows = cur.execute(
        "SELECT prioridad, COUNT(*) AS c FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (id,)
    ).fetchall()
    por_prioridad: Dict[str, int] = {r["prioridad"]: r["c"] for r in por_prioridad_rows}
    for p in VALID_PRIORIDADES:
        por_prioridad.setdefault(p, 0)

    conn.close()
    return ResumenProyectoOut(
        proyecto_id=proy["id"],
        proyecto_nombre=proy["nombre"],
        total_tareas=total,
        por_estado=por_estado,
        por_prioridad=por_prioridad
    )


@app.get("/resumen", response_model=ResumenGlobalOut)
def resumen_global():
    conn = get_connection()
    cur = conn.cursor()

    total_proyectos = cur.execute("SELECT COUNT(*) AS c FROM proyectos").fetchone()["c"]
    total_tareas = cur.execute("SELECT COUNT(*) AS c FROM tareas").fetchone()["c"]

    # tareas por estado
    tpe_rows = cur.execute("SELECT estado, COUNT(*) AS c FROM tareas GROUP BY estado").fetchall()
    tareas_por_estado: Dict[str, int] = {r["estado"]: r["c"] for r in tpe_rows}
    for e in VALID_ESTADOS:
        tareas_por_estado.setdefault(e, 0)

    # proyecto con más tareas
    top = cur.execute(
        "SELECT p.id, p.nombre, COUNT(t.id) AS cantidad "
        "FROM proyectos p LEFT JOIN tareas t ON t.proyecto_id = p.id "
        "GROUP BY p.id "
        "ORDER BY cantidad DESC "
        "LIMIT 1"
    ).fetchone()

    conn.close()

    proyecto_con_mas_tareas = None
    if top and (top["cantidad"] or top["cantidad"] == 0):
        proyecto_con_mas_tareas = {
            "id": top["id"],
            "nombre": top["nombre"],
            "cantidad_tareas": top["cantidad"]
        }

    return ResumenGlobalOut(
        total_proyectos=total_proyectos,
        total_tareas=total_tareas,
        tareas_por_estado=tareas_por_estado,
        proyecto_con_mas_tareas=proyecto_con_mas_tareas
    )

