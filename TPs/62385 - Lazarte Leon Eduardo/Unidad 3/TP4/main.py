from fastapi import FastAPI, HTTPException
from typing import Optional
import sqlite3
from datetime import datetime
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate

app = FastAPI(title="API Proyectos y Tareas - TP4")

DB_NAME = "tareas.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===================== PROYECTOS =====================

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = get_db()
    try:
        if nombre:
            proyectos = conn.execute(
                '''SELECT p.*, COALESCE(COUNT(t.id), 0) as total_tareas
                   FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
                   WHERE p.nombre LIKE ? GROUP BY p.id''',
                (f'%{nombre}%',)
            ).fetchall()
        else:
            proyectos = conn.execute(
                '''SELECT p.*, COALESCE(COUNT(t.id), 0) as total_tareas
                   FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
                   GROUP BY p.id'''
            ).fetchall()
        return [dict(p) for p in proyectos]
    finally:
        conn.close()

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_db()
    try:
        proyecto = conn.execute(
            '''SELECT p.*, COALESCE(COUNT(t.id), 0) as total_tareas
               FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
               WHERE p.id = ? GROUP BY p.id''',
            (id,)
        ).fetchone()
        if not proyecto:
            raise HTTPException(404, "Proyecto no encontrado")
        return dict(proyecto)
    finally:
        conn.close()

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_db()
    try:
        cursor = conn.execute(
            'INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)',
            (proyecto.nombre, proyecto.descripcion, datetime.now().isoformat())
        )
        conn.commit()
        return obtener_proyecto(cursor.lastrowid)
    except sqlite3.IntegrityError:
        raise HTTPException(409, f"Ya existe un proyecto con el nombre '{proyecto.nombre}'")
    finally:
        conn.close()

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_db()
    updates = []
    params = []
    if proyecto.nombre is not None:
        updates.append('nombre = ?')
        params.append(proyecto.nombre)
    if proyecto.descripcion is not None:
        updates.append('descripcion = ?')
        params.append(proyecto.descripcion)
    if updates:
        params.append(id)
        try:
            conn.execute(f'UPDATE proyectos SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, f"Ya existe un proyecto con el nombre '{proyecto.nombre}'")
    result = obtener_proyecto(id)
    conn.close()
    return result

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_db()
    try:
        tareas_count = conn.execute('SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?', (id,)).fetchone()[0]
        cursor = conn.execute('DELETE FROM proyectos WHERE id = ?', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Proyecto no encontrado")
        return {"message": "Proyecto eliminado correctamente", "tareas_eliminadas": tareas_count}
    finally:
        conn.close()

# ===================== TAREAS =====================

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(id: int, estado: Optional[str] = None, prioridad: Optional[str] = None, orden: str = "desc"):
    conn = get_db()
    try:
        if not conn.execute('SELECT 1 FROM proyectos WHERE id = ?', (id,)).fetchone():
            raise HTTPException(404, "Proyecto no encontrado")
        query = '''SELECT t.*, p.nombre as proyecto_nombre
                   FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id
                   WHERE t.proyecto_id = ?'''
        params = [id]
        if estado:
            query += ' AND t.estado = ?'
            params.append(estado)
        if prioridad:
            query += ' AND t.prioridad = ?'
            params.append(prioridad)
        query += f' ORDER BY t.fecha_creacion {"ASC" if orden == "asc" else "DESC"}'
        tareas = conn.execute(query, params).fetchall()
        return [dict(t) for t in tareas]
    finally:
        conn.close()

@app.get("/tareas")
def listar_tareas(proyecto_id: Optional[int] = None, estado: Optional[str] = None,
                  prioridad: Optional[str] = None, orden: str = "desc"):
    conn = get_db()
    try:
        query = '''SELECT t.*, p.nombre as proyecto_nombre
                   FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id
                   WHERE 1=1'''
        params = []
        if proyecto_id:
            query += ' AND t.proyecto_id = ?'
            params.append(proyecto_id)
        if estado:
            query += ' AND t.estado = ?'
            params.append(estado)
        if prioridad:
            query += ' AND t.prioridad = ?'
            params.append(prioridad)
        query += f' ORDER BY t.fecha_creacion {"ASC" if orden == "asc" else "DESC"}'
        tareas = conn.execute(query, params).fetchall()
        return [dict(t) for t in tareas]
    finally:
        conn.close()

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    conn = get_db()
    try:
        if not conn.execute('SELECT 1 FROM proyectos WHERE id = ?', (id,)).fetchone():
            raise HTTPException(400, f"El proyecto con ID {id} no existe")
        cursor = conn.execute(
            'INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
            (tarea.descripcion, tarea.estado, tarea.prioridad, id, datetime.now().isoformat())
        )
        conn.commit()
        tarea_id = cursor.lastrowid
        tarea_creada = conn.execute(
            'SELECT t.*, p.nombre as proyecto_nombre FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id WHERE t.id = ?',
            (tarea_id,)
        ).fetchone()
        return dict(tarea_creada)
    finally:
        conn.close()

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db()
    try:
        if not conn.execute('SELECT 1 FROM tareas WHERE id = ?', (id,)).fetchone():
            raise HTTPException(404, "Tarea no encontrada")
        if tarea.proyecto_id is not None and not conn.execute('SELECT 1 FROM proyectos WHERE id = ?', (tarea.proyecto_id,)).fetchone():
            raise HTTPException(400, f"El proyecto con ID {tarea.proyecto_id} no existe")

        updates = []
        params = []
        if tarea.descripcion is not None:
            updates.append('descripcion = ?')
            params.append(tarea.descripcion)
        if tarea.estado is not None:
            updates.append('estado = ?')
            params.append(tarea.estado)
        if tarea.prioridad is not None:
            updates.append('prioridad = ?')
            params.append(tarea.prioridad)
        if tarea.proyecto_id is not None:
            updates.append('proyecto_id = ?')
            params.append(tarea.proyecto_id)
        if updates:
            params.append(id)
            conn.execute(f'UPDATE tareas SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        tarea_actualizada = conn.execute(
            'SELECT t.*, p.nombre as proyecto_nombre FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id WHERE t.id = ?',
            (id,)
        ).fetchone()
        return dict(tarea_actualizada)
    finally:
        conn.close()

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db()
    try:
        cursor = conn.execute('DELETE FROM tareas WHERE id = ?', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Tarea no encontrada")
        return {"message": "Tarea eliminada correctamente"}
    finally:
        conn.close()

# ===================== RESUMEN =====================

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_db()
    try:
        proyecto = conn.execute('SELECT * FROM proyectos WHERE id = ?', (id,)).fetchone()
        if not proyecto:
            raise HTTPException(404, "Proyecto no encontrado")
        estados = conn.execute('SELECT estado, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY estado', (id,)).fetchall()
        prioridades = conn.execute('SELECT prioridad, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY prioridad', (id,)).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?', (id,)).fetchone()[0]
        return {
            "proyecto_id": id,
            "proyecto_nombre": proyecto['nombre'],
            "total_tareas": total,
            "por_estado": {row['estado']: row['cantidad'] for row in estados},
            "por_prioridad": {row['prioridad']: row['cantidad'] for row in prioridades}
        }
    finally:
        conn.close()

@app.get("/resumen")
def resumen_general():
    conn = get_db()
    try:
        total_proyectos = conn.execute('SELECT COUNT(*) FROM proyectos').fetchone()[0]
        total_tareas = conn.execute('SELECT COUNT(*) FROM tareas').fetchone()[0]
        estados = conn.execute('SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado').fetchall()
        top = conn.execute('''
            SELECT p.id, p.nombre, COALESCE(COUNT(t.id), 0) as cantidad_tareas
            FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id ORDER BY cantidad_tareas DESC LIMIT 1
        ''').fetchone()
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": {row['estado']: row['cantidad'] for row in estados} if estados else {},
            "proyecto_con_mas_tareas": {
                "id": top['id'],
                "nombre": top['nombre'],
                "cantidad_tareas": top['cantidad_tareas']
            } if top and top['cantidad_tareas'] > 0 else None
        }
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)