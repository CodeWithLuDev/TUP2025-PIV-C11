from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from pathlib import Path

from database import init_db, get_connection
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate

DB_NAME = str(Path(__file__).parent / "tareas.db")

app = FastAPI(title="TP4 - Proyectos y Tareas")

@app.on_event("startup")
def startup():
    init_db()

# ---------- PROYECTOS ----------
@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None, description="Texto parcial a buscar en nombre")):
    conn = get_connection()
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE nombre LIKE ? ORDER BY id",
                    (f"%{nombre}%",))
    else:
        cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos ORDER BY id")
    filas = [dict(row) for row in cur.fetchall()]
    conn.close()
    return filas

@app.get("/proyectos/{proyecto_id}")
def obtener_proyecto(proyecto_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    cur.execute("SELECT COUNT(*) as total_tareas FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total = cur.fetchone()["total_tareas"]
    resultado = dict(proyecto)
    resultado["total_tareas"] = total
    conn.close()
    return resultado

@app.post("/proyectos", status_code=201)
def crear_proyecto(p: ProyectoCreate):
    conn = get_connection()
    cur = conn.cursor()
    # verificar duplicado
    cur.execute("SELECT id FROM proyectos WHERE nombre = ?", (p.nombre,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    cur.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (p.nombre, p.descripcion, p.fecha_creacion)
    )
    conn.commit()
    pid = cur.lastrowid
    cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (pid,))
    proyecto = dict(cur.fetchone())
    conn.close()
    return proyecto

@app.put("/proyectos/{proyecto_id}")
def modificar_proyecto(proyecto_id: int, p: ProyectoUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if p.nombre is not None:
        # verificar duplicado en otro id
        cur.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (p.nombre, proyecto_id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Otro proyecto ya utiliza ese nombre")
        cur.execute("UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?",
                    (p.nombre, p.descripcion, proyecto_id))
    else:
        cur.execute("UPDATE proyectos SET descripcion = ? WHERE id = ?", (p.descripcion, proyecto_id))
    conn.commit()
    cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = dict(cur.fetchone())
    conn.close()
    return proyecto

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    # contar tareas asociadas antes de eliminar
    cur.execute("SELECT COUNT(*) as c FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_c = cur.fetchone()["c"]
    cur.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    return {"tareas_eliminadas": tareas_c}

# ---------- TAREAS ----------
def _aplicar_filtros(base_sql: str, estado: Optional[str], prioridad: Optional[str], proyecto_id: Optional[int], orden: Optional[str]):
    condiciones = []
    valores = []
    if estado:
        condiciones.append("estado = ?")
        valores.append(estado)
    if prioridad:
        condiciones.append("prioridad = ?")
        valores.append(prioridad)
    if proyecto_id is not None:
        condiciones.append("proyecto_id = ?")
        valores.append(proyecto_id)
    sql = base_sql
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    if orden and orden.lower() in ("asc", "desc"):
        sql += f" ORDER BY fecha_creacion {orden.upper()}"
    else:
        sql += " ORDER BY id"
    return sql, valores

@app.get("/tareas")
def listar_tareas(estado: Optional[str] = None, prioridad: Optional[str] = None, proyecto_id: Optional[int] = None, orden: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    base = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas"
    sql, vals = _aplicar_filtros(base, estado, prioridad, proyecto_id, orden)
    cur.execute(sql, tuple(vals))
    filas = [dict(row) for row in cur.fetchall()]
    conn.close()
    return filas

@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_proyecto(proyecto_id: int, estado: Optional[str] = None, prioridad: Optional[str] = None, orden: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    base = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas"
    sql, vals = _aplicar_filtros(base, estado, prioridad, proyecto_id, orden)
    cur.execute(sql, tuple(vals))
    filas = [dict(row) for row in cur.fetchall()]
    conn.close()
    return filas

@app.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea(proyecto_id: int, t: TareaCreate):
    conn = get_connection()
    cur = conn.cursor()
    # validar proyecto existe
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto indicado no existe")
    cur.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (t.descripcion, t.estado, t.prioridad, proyecto_id, t.fecha_creacion)
    )
    conn.commit()
    tid = cur.lastrowid
    cur.execute("SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE id = ?", (tid,))
    tarea = dict(cur.fetchone())
    conn.close()
    return tarea

@app.put("/tareas/{tarea_id}")
def modificar_tarea(tarea_id: int, t: TareaUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    # si se cambia proyecto, validar existencia
    if t.proyecto_id is not None:
        cur.execute("SELECT id FROM proyectos WHERE id = ?", (t.proyecto_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto indicado para la tarea no existe")
    # construir update dinámico
    campos = []
    valores = []
    if t.descripcion is not None:
        campos.append("descripcion = ?"); valores.append(t.descripcion)
    if t.estado is not None:
        campos.append("estado = ?"); valores.append(t.estado)
    if t.prioridad is not None:
        campos.append("prioridad = ?"); valores.append(t.prioridad)
    if t.proyecto_id is not None:
        campos.append("proyecto_id = ?"); valores.append(t.proyecto_id)
    if campos:
        sql = "UPDATE tareas SET " + ", ".join(campos) + " WHERE id = ?"
        valores.append(tarea_id)
        cur.execute(sql, tuple(valores))
        conn.commit()
    cur.execute("SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE id = ?", (tarea_id,))
    tarea = dict(cur.fetchone())
    conn.close()
    return tarea

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}

# ---------- RESÚMENES ----------
@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    cur.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total = cur.fetchone()["total"]
    cur.execute("SELECT estado, COUNT(*) as c FROM tareas WHERE proyecto_id = ? GROUP BY estado", (proyecto_id,))
    por_estado = {row["estado"]: row["c"] for row in cur.fetchall()}
    cur.execute("SELECT prioridad, COUNT(*) as c FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (proyecto_id,))
    por_prioridad = {row["prioridad"]: row["c"] for row in cur.fetchall()}
    conn.close()
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total_proyectos FROM proyectos")
    total_proyectos = cur.fetchone()["total_proyectos"]
    cur.execute("SELECT COUNT(*) as total_tareas FROM tareas")
    total_tareas = cur.fetchone()["total_tareas"]
    cur.execute("SELECT estado, COUNT(*) as c FROM tareas GROUP BY estado")
    tareas_por_estado = {row["estado"]: row["c"] for row in cur.fetchall()}
    cur.execute("""SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
                   FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
                   GROUP BY p.id ORDER BY cantidad_tareas DESC LIMIT 1""")
    top = cur.fetchone()
    proyecto_con_mas = {"id": top["id"], "nombre": top["nombre"], "cantidad_tareas": top["cantidad_tareas"]} if top else None
    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas
    }