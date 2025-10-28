from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3

from models import (
    ProyectoCreate,
    ProyectoUpdate,
    TareaCreate,
    TareaUpdate,
)
from database import init_db, get_connection, DB_NAME

app = FastAPI(title="TP4 - Proyectos y Tareas")

# Re-exportar para que los tests puedan importarlos desde main
# (init_db y DB_NAME vienen de database.py)

# Helpers
def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

# ========== Endpoints Proyectos ==========

@app.post("/proyectos", status_code=201)
def crear_proyecto(payload: ProyectoCreate):
    conn = get_connection()
    cursor = conn.cursor()
    # Validar nombre único
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (payload.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    fecha = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (payload.nombre, payload.descripcion, fecha),
    )
    proyecto_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    conn = get_connection()
    cursor = conn.cursor()
    if nombre:
        like = f"%{nombre}%"
        cursor.execute("SELECT * FROM proyectos WHERE nombre LIKE ? ORDER BY id", (like,))
    else:
        cursor.execute("SELECT * FROM proyectos ORDER BY id")
    filas = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in filas]

@app.get("/proyectos/{proyecto_id}")
def obtener_proyecto(proyecto_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proj = cursor.fetchone()
    if not proj:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    proj_d = row_to_dict(proj)
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total = cursor.fetchone()["total"]
    proj_d["total_tareas"] = total
    conn.close()
    return proj_d

@app.put("/proyectos/{proyecto_id}")
def actualizar_proyecto(proyecto_id: int, payload: ProyectoUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    # Si nombre provisto, validar duplicado (excluyendo el proyecto actual)
    if payload.nombre:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (payload.nombre, proyecto_id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Ya existe otro proyecto con ese nombre")
    # Construir update dinámico
    updates = []
    params = []
    if payload.nombre is not None:
        updates.append("nombre = ?")
        params.append(payload.nombre)
    if payload.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(payload.descripcion)
    if updates:
        params.append(proyecto_id)
        sql = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, tuple(params))
        conn.commit()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    # Contar tareas antes de borrar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total = cursor.fetchone()["total"]
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    return {"message": "Proyecto eliminado", "tareas_eliminadas": total}

# ========== Endpoints Tareas ==========

@app.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea_en_proyecto(proyecto_id: int, payload: TareaCreate):
    conn = get_connection()
    cursor = conn.cursor()
    # Verificar proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El proyecto indicado no existe")
    fecha = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (payload.descripcion, payload.estado, payload.prioridad, proyecto_id, fecha),
    )
    tarea_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_de_proyecto(proyecto_id: int, estado: Optional[str] = None, prioridad: Optional[str] = None, orden: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    # Verificar proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [proyecto_id]
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    order_clause = " ORDER BY fecha_creacion "
    if orden and orden.lower() == "desc":
        order_clause += "DESC"
    else:
        order_clause += "ASC"
    query += order_clause
    cursor.execute(query, tuple(params))
    filas = cursor.fetchall()
    conn.close()
    return [row_to_dict(f) for f in filas]

@app.get("/tareas")
def listar_todas_las_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tareas"
    conditions = []
    params = []
    if proyecto_id is not None:
        conditions.append("proyecto_id = ?")
        params.append(proyecto_id)
    if estado:
        conditions.append("estado = ?")
        params.append(estado)
    if prioridad:
        conditions.append("prioridad = ?")
        params.append(prioridad)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    # Orden
    if orden and orden.lower() == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    cursor.execute(query, tuple(params))
    filas = cursor.fetchall()
    conn.close()
    return [row_to_dict(f) for f in filas]

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, payload: TareaUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    # Si proyecto_id provisto, verificar que exista
    if payload.proyecto_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (payload.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto indicado no existe")
    updates = []
    params = []
    if payload.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(payload.descripcion)
    if payload.estado is not None:
        updates.append("estado = ?")
        params.append(payload.estado)
    if payload.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(payload.prioridad)
    if payload.proyecto_id is not None:
        updates.append("proyecto_id = ?")
        params.append(payload.proyecto_id)
    if updates:
        params.append(tarea_id)
        sql = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, tuple(params))
        conn.commit()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    return {"message": "Tarea eliminada"}

# ========== Endpoints Resumen ==========

@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    proyecto_nombre = proyecto["nombre"]
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    # Por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cnt FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    por_estado_rows = cursor.fetchall()
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for r in por_estado_rows:
        por_estado[r["estado"]] = r["cnt"]
    # Por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cnt FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    por_prioridad_rows = cursor.fetchall()
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for r in por_prioridad_rows:
        por_prioridad[r["prioridad"]] = r["cnt"]
    conn.close()
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto_nombre,
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
    }

@app.get("/resumen")
def resumen_general():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    cursor.execute("SELECT estado, COUNT(*) as cnt FROM tareas GROUP BY estado")
    filas_estado = cursor.fetchall()
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for r in filas_estado:
        tareas_por_estado[r["estado"]] = r["cnt"]
    # Proyecto con más tareas
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    top = cursor.fetchone()
    if top:
        proyecto_con_mas = {"id": top["id"], "nombre": top["nombre"], "cantidad_tareas": top["cantidad_tareas"]}
    else:
        proyecto_con_mas = None
    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas,
    }
