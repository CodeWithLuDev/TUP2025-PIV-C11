# main.py
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
from typing import Optional, List, Dict
import sqlite3

from database import init_db, get_conn, DB_NAME
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate, ESTADOS, PRIORIDADES

# Inicializa DB (crea tablas si no existen)
init_db()

app = FastAPI(title="API Proyectos y Tareas")

# ---------- Root y home ----------
@app.get("/")
def root():
    return {"mensaje": "API Proyectos y Tareas - funcionando"}

@app.get("/home", response_class=HTMLResponse, include_in_schema=False)
def home():
    return """
    <html>
      <head><title>API Proyectos y Tareas</title></head>
      <body>
        <h1>API Proyectos y Tareas</h1>
        <p>Usá <code>/docs</code> para ver la documentación interactiva.</p>
      </body>
    </html>
    """

# --------------------------
# CRUD PROYECTOS
# --------------------------
@app.post("/proyectos", status_code=201)
def crear_proyecto(payload: ProyectoCreate):
    nombre = payload.nombre
    descripcion = payload.descripcion
    fecha_creacion = datetime.now().isoformat()

    conn = get_conn()
    cur = conn.cursor()
    # verificar duplicado
    cur.execute("SELECT id FROM proyectos WHERE nombre = ?", (nombre,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")

    cur.execute("""
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    """, (nombre, descripcion, fecha_creacion))
    conn.commit()
    nuevo_id = cur.lastrowid
    cur.execute("SELECT * FROM proyectos WHERE id = ?", (nuevo_id,))
    fila = cur.fetchone()
    conn.close()

    return {"id": fila[0], "nombre": fila[1], "descripcion": fila[2], "fecha_creacion": fila[3]}

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None, description="Filtro por texto parcial en nombre")):
    conn = get_conn()
    cur = conn.cursor()
    if nombre:
        cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE nombre LIKE ? COLLATE NOCASE", (f"%{nombre}%",))
    else:
        cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos")
    filas = cur.fetchall()
    conn.close()
    return [{"id": f[0], "nombre": f[1], "descripcion": f[2], "fecha_creacion": f[3]} for f in filas]

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (id,))
    proyecto = cur.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    # contar tareas asociadas
    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cur.fetchone()[0]
    conn.close()
    return {
        "id": proyecto[0],
        "nombre": proyecto[1],
        "descripcion": proyecto[2],
        "fecha_creacion": proyecto[3],
        "total_tareas": total_tareas
    }

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, payload: ProyectoUpdate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Si se provee nombre, validar duplicado
    if payload.nombre:
        cur.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (payload.nombre, id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Ya existe otro proyecto con ese nombre")

    campos = []
    valores = []
    if payload.nombre is not None:
        campos.append("nombre = ?")
        valores.append(payload.nombre)
    if payload.descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(payload.descripcion)

    if campos:
        valores.append(id)
        sql = f"UPDATE proyectos SET {', '.join(campos)} WHERE id = ?"
        cur.execute(sql, valores)
        conn.commit()

    cur.execute("SELECT id, nombre, descripcion, fecha_creacion FROM proyectos WHERE id = ?", (id,))
    fila = cur.fetchone()
    conn.close()

    return {"id": fila[0], "nombre": fila[1], "descripcion": fila[2], "fecha_creacion": fila[3]}

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_conn()
    cur = conn.cursor()

    # Verificar existencia del proyecto
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Contar tareas asociadas antes de borrar
    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_asociadas = cur.fetchone()[0]

    # Eliminar proyecto (las tareas se eliminan automáticamente por ON DELETE CASCADE)
    cur.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {
        "mensaje": f"Proyecto {id} eliminado correctamente",
        "tareas_eliminadas": tareas_asociadas
    }

# --------------------------
# TAREAS (global y por proyecto)
# --------------------------

def _build_tareas_query(filters: dict):
    # devuelve (sql, params)
    base = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE 1=1"
    params = []
    if filters.get("estado"):
        base += " AND estado = ?"
        params.append(filters["estado"])
    if filters.get("prioridad"):
        base += " AND prioridad = ?"
        params.append(filters["prioridad"])
    if filters.get("proyecto_id") is not None:
        base += " AND proyecto_id = ?"
        params.append(filters["proyecto_id"])
    if filters.get("texto"):
        base += " AND descripcion LIKE ? COLLATE NOCASE"
        params.append(f"%{filters['texto']}%")
    orden = filters.get("orden", "asc").lower()
    if orden not in ("asc", "desc"):
        orden = "asc"
    base += f" ORDER BY fecha_creacion {orden.upper()}"
    return base, params

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    texto: Optional[str] = None,
    orden: str = "asc"
):
    # Validaciones simples
    if estado and estado not in ESTADOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    if prioridad and prioridad not in PRIORIDADES:
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    filters = {"estado": estado, "prioridad": prioridad, "proyecto_id": proyecto_id, "texto": texto, "orden": orden}
    sql, params = _build_tareas_query(filters)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    filas = cur.fetchall()
    conn.close()

    return [
        {"id": f[0], "descripcion": f[1], "estado": f[2], "prioridad": f[3], "proyecto_id": f[4], "fecha_creacion": f[5]}
        for f in filas
    ]

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(id: int,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    texto: Optional[str] = None,
    orden: str = "asc"
):
    # validar proyecto existe
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # validaciones
    if estado and estado not in ESTADOS:
        conn.close()
        raise HTTPException(status_code=400, detail="Estado inválido")
    if prioridad and prioridad not in PRIORIDADES:
        conn.close()
        raise HTTPException(status_code=400, detail="Prioridad inválida")

    filters = {"estado": estado, "prioridad": prioridad, "proyecto_id": id, "texto": texto, "orden": orden}
    sql, params = _build_tareas_query(filters)
    cur.execute(sql, params)
    filas = cur.fetchall()
    conn.close()

    return [
        {"id": f[0], "descripcion": f[1], "estado": f[2], "prioridad": f[3], "proyecto_id": f[4], "fecha_creacion": f[5]}
        for f in filas
    ]

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea_en_proyecto(id: int, payload: TareaCreate):
    # validar proyecto existe
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto indicado no existe")

    # insertar tarea
    fecha_creacion = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (payload.descripcion, payload.estado, payload.prioridad, id, fecha_creacion))
    conn.commit()
    nueva_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (nueva_id,))
    fila = cur.fetchone()
    conn.close()

    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "prioridad": fila[3],
        "proyecto_id": fila[4],
        "fecha_creacion": fila[5]
    }

@app.post("/tareas", status_code=201)
def crear_tarea_global(payload: TareaCreate):
    # si payload.proyecto_id se proporciona, validar
    conn = get_conn()
    cur = conn.cursor()
    if payload.proyecto_id is not None:
        cur.execute("SELECT id FROM proyectos WHERE id = ?", (payload.proyecto_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto indicado no existe")

    fecha_creacion = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (payload.descripcion, payload.estado, payload.prioridad, payload.proyecto_id, fecha_creacion))
    conn.commit()
    nueva_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (nueva_id,))
    fila = cur.fetchone()
    conn.close()

    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "prioridad": fila[3],
        "proyecto_id": fila[4],
        "fecha_creacion": fila[5]
    }

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, payload: TareaUpdate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cur.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # si se cambia proyecto_id, validar existe (y puede ser None)
    if payload.proyecto_id is not None:
        cur.execute("SELECT id FROM proyectos WHERE id = ?", (payload.proyecto_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto indicado no existe")

    campos = []
    vals = []
    if payload.descripcion is not None:
        campos.append("descripcion = ?"); vals.append(payload.descripcion)
    if payload.estado is not None:
        if payload.estado not in ESTADOS:
            conn.close()
            raise HTTPException(status_code=400, detail="Estado inválido")
        campos.append("estado = ?"); vals.append(payload.estado)
    if payload.prioridad is not None:
        if payload.prioridad not in PRIORIDADES:
            conn.close()
            raise HTTPException(status_code=400, detail="Prioridad inválida")
        campos.append("prioridad = ?"); vals.append(payload.prioridad)
    if "proyecto_id" in payload.__dict__ and payload.proyecto_id is not None:
        campos.append("proyecto_id = ?"); vals.append(payload.proyecto_id)
    # Allow to set proyecto_id to NULL by sending {"proyecto_id": null} in JSON:
    if "proyecto_id" in payload.__dict__ and payload.proyecto_id is None:
        campos.append("proyecto_id = ?"); vals.append(None)

    if campos:
        vals.append(id)
        sql = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
        cur.execute(sql, vals)
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    f = cur.fetchone()
    conn.close()
    return {"id": f[0], "descripcion": f[1], "estado": f[2], "prioridad": f[3], "proyecto_id": f[4], "fecha_creacion": f[5]}

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM tareas WHERE id = ?", (id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cur.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": f"Tarea {id} eliminada correctamente"}

# --------------------------
# RESUMEN / ESTADISTICAS
# --------------------------

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM proyectos WHERE id = ?", (id,))
    p = cur.fetchone()
    if not p:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # total tareas
    cur.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    total = cur.fetchone()[0]

    # por estado
    cur.execute("SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY estado", (id,))
    filas_estado = cur.fetchall()
    por_estado = {e: 0 for e in ESTADOS}
    for estado, cnt in filas_estado:
        por_estado[estado] = cnt

    # por prioridad
    cur.execute("SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (id,))
    filas_prio = cur.fetchall()
    por_prioridad = {p: 0 for p in PRIORIDADES}
    for prio, cnt in filas_prio:
        por_prioridad[prio] = cnt

    conn.close()
    return {
        "proyecto_id": p[0],
        "proyecto_nombre": p[1],
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_global():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cur.fetchone()[0]

    # tareas por estado
    cur.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    filas_estado = cur.fetchall()
    tareas_por_estado = {e: 0 for e in ESTADOS}
    for estado, cnt in filas_estado:
        tareas_por_estado[estado] = cnt

    # proyecto con mas tareas
    cur.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad
        FROM proyectos p
        LEFT JOIN tareas t ON t.proyecto_id = p.id
        GROUP BY p.id
        ORDER BY cantidad DESC
        LIMIT 1
    """)
    top = cur.fetchone()
    proyecto_top = {"id": None, "nombre": None, "cantidad_tareas": 0}
    if top:
        proyecto_top = {"id": top[0], "nombre": top[1], "cantidad_tareas": top[2]}

    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_top
    }
