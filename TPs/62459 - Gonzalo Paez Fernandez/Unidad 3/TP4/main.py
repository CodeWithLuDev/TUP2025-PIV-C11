from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
import sqlite3

from database import get_db_connection, init_db
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate

app = FastAPI(title="TP4 - Proyectos y Tareas (Relaciones SQLite)")
init_db()


# -------------------------------
# CRUD de Proyectos
# -------------------------------
@app.get("/proyectos")
def listar_proyectos(nombre: str | None = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos")

    proyectos = cursor.fetchall()
    conn.close()
    return [dict(p) for p in proyectos]


@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()

    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id=?", (id,))
    tareas_count = cursor.fetchone()["total"]

    conn.close()
    return {**dict(proyecto), "cantidad_tareas": tareas_count}


@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    if not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del proyecto no puede estar vacío.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validar duplicados
    cursor.execute("SELECT * FROM proyectos WHERE nombre=?", (proyecto.nombre,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre.")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha),
    )
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {"id": nuevo_id, "nombre": proyecto.nombre, "descripcion": proyecto.descripcion, "fecha_creacion": fecha}


@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, datos: ProyectoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    if datos.nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre=? AND id<>?", (datos.nombre, id))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Ya existe otro proyecto con ese nombre.")

    campos = []
    valores = []

    if datos.nombre:
        campos.append("nombre=?")
        valores.append(datos.nombre)
    if datos.descripcion is not None:
        campos.append("descripcion=?")
        valores.append(datos.descripcion)

    if not campos:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar.")

    valores.append(id)
    cursor.execute(f"UPDATE proyectos SET {', '.join(campos)} WHERE id=?", valores)
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto actualizado correctamente."}


@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    cursor.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto y sus tareas eliminados correctamente."}


# -------------------------------
# CRUD de Tareas
# -------------------------------
@app.get("/tareas")
def listar_tareas(
    estado: str | None = None,
    prioridad: str | None = None,
    proyecto_id: int | None = None,
    orden: str | None = Query(None, pattern="^(asc|desc)$")
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
    if orden:
        query += f" ORDER BY fecha_creacion {orden.upper()}"

    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    return [dict(t) for t in tareas]


@app.get("/proyectos/{id}/tareas")
def listar_tareas_por_proyecto(id: int, estado: str | None = None, prioridad: str | None = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    query = "SELECT * FROM tareas WHERE proyecto_id=?"
    params = [id]
    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)

    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    return [dict(t) for t in tareas]


@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="El proyecto_id no existe.")

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha))
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()

    return {"id": nuevo_id, "mensaje": "Tarea creada correctamente."}


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, datos: TareaUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    campos = []
    valores = []

    if datos.descripcion:
        campos.append("descripcion=?")
        valores.append(datos.descripcion)
    if datos.estado:
        campos.append("estado=?")
        valores.append(datos.estado)
    if datos.prioridad:
        campos.append("prioridad=?")
        valores.append(datos.prioridad)
    if datos.proyecto_id:
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (datos.proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="El nuevo proyecto_id no existe.")
        campos.append("proyecto_id=?")
        valores.append(datos.proyecto_id)

    if not campos:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar.")

    valores.append(id)
    cursor.execute(f"UPDATE tareas SET {', '.join(campos)} WHERE id=?", valores)
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea actualizada correctamente."}


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente."}


# -------------------------------
# Resúmenes y Estadísticas
# -------------------------------
@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cursor.fetchone()["total"]

    def contar_por(campo):
        cursor.execute(f"SELECT {campo}, COUNT(*) as cantidad FROM tareas WHERE proyecto_id=? GROUP BY {campo}", (id,))
        return {r[campo]: r["cantidad"] for r in cursor.fetchall()}

    por_estado = contar_por("estado")
    por_prioridad = contar_por("prioridad")

    conn.close()

    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


@app.get("/resumen")
def resumen_general():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]

    cursor.execute("SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado")
    tareas_por_estado = {r["estado"]: r["cantidad"] for r in cursor.fetchall()}

    cursor.execute("""
        SELECT proyectos.id, proyectos.nombre, COUNT(tareas.id) as cantidad_tareas
        FROM proyectos LEFT JOIN tareas ON proyectos.id = tareas.proyecto_id
        GROUP BY proyectos.id
        ORDER BY cantidad_tareas DESC LIMIT 1
    """)
    top = cursor.fetchone()

    conn.close()

    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": {
            "id": top["id"],
            "nombre": top["nombre"],
            "cantidad_tareas": top["cantidad_tareas"]
        } if top else None
    }
