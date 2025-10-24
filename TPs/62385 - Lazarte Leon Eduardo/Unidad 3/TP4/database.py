import sqlite3
from datetime import datetime
from typing import Optional

def get_db_connection():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        fecha_creacion TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        prioridad TEXT NOT NULL,
        proyecto_id INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()

# PROYECTOS
def crear_proyecto(nombre: str, descripcion: Optional[str] = None):
    conn = get_db_connection()
    try:
        cursor = conn.execute('INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)',
                            (nombre, descripcion, datetime.now().isoformat()))
        conn.commit()
        proyecto_id = cursor.lastrowid
        conn.close()
        return obtener_proyecto(proyecto_id)
    except sqlite3.IntegrityError:
        conn.close()
        return None

def obtener_proyectos(nombre_busqueda: Optional[str] = None):
    conn = get_db_connection()
    if nombre_busqueda:
        proyectos = conn.execute(
            'SELECT p.*, COUNT(t.id) as total_tareas FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id WHERE p.nombre LIKE ? GROUP BY p.id',
            (f'%{nombre_busqueda}%',)).fetchall()
    else:
        proyectos = conn.execute(
            'SELECT p.*, COUNT(t.id) as total_tareas FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id GROUP BY p.id').fetchall()
    conn.close()
    return [dict(p) for p in proyectos]

def obtener_proyecto(proyecto_id: int):
    conn = get_db_connection()
    proyecto = conn.execute(
        'SELECT p.*, COUNT(t.id) as total_tareas FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id WHERE p.id = ? GROUP BY p.id',
        (proyecto_id,)).fetchone()
    conn.close()
    return dict(proyecto) if proyecto else None

def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, descripcion: Optional[str] = None):
    conn = get_db_connection()
    proyecto = obtener_proyecto(proyecto_id)
    if not proyecto:
        conn.close()
        return None
    updates = []
    params = []
    if nombre is not None:
        updates.append('nombre = ?')
        params.append(nombre)
    if descripcion is not None:
        updates.append('descripcion = ?')
        params.append(descripcion)
    if updates:
        params.append(proyecto_id)
        try:
            conn.execute(f'UPDATE proyectos SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return None
    conn.close()
    return obtener_proyecto(proyecto_id)

def eliminar_proyecto(proyecto_id: int):
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM proyectos WHERE id = ?', (proyecto_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

# TAREAS
def crear_tarea(descripcion: str, estado: str, prioridad: str, proyecto_id: int):
    conn = get_db_connection()
    if not conn.execute('SELECT id FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone():
        conn.close()
        return None
    cursor = conn.execute(
        'INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
        (descripcion, estado, prioridad, proyecto_id, datetime.now().isoformat()))
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    return obtener_tarea(tarea_id)

def obtener_tareas(proyecto_id: Optional[int] = None, estado: Optional[str] = None,
                  prioridad: Optional[str] = None, orden: str = "desc"):
    conn = get_db_connection()
    query = 'SELECT t.*, p.nombre as proyecto_nombre FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id WHERE 1=1'
    params = []
    if proyecto_id is not None:
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
    conn.close()
    return [dict(t) for t in tareas]

def obtener_tarea(tarea_id: int):
    conn = get_db_connection()
    tarea = conn.execute(
        'SELECT t.*, p.nombre as proyecto_nombre FROM tareas t JOIN proyectos p ON t.proyecto_id = p.id WHERE t.id = ?',
        (tarea_id,)).fetchone()
    conn.close()
    return dict(tarea) if tarea else None

def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None, estado: Optional[str] = None,
                    prioridad: Optional[str] = None, proyecto_id: Optional[int] = None):
    conn = get_db_connection()
    if not obtener_tarea(tarea_id):
        conn.close()
        return None
    if proyecto_id is not None and not conn.execute('SELECT id FROM proyectos WHERE id = ?', (proyecto_id,)).fetchone():
        conn.close()
        return None
    updates = []
    params = []
    if descripcion is not None:
        updates.append('descripcion = ?')
        params.append(descripcion)
    if estado is not None:
        updates.append('estado = ?')
        params.append(estado)
    if prioridad is not None:
        updates.append('prioridad = ?')
        params.append(prioridad)
    if proyecto_id is not None:
        updates.append('proyecto_id = ?')
        params.append(proyecto_id)
    if updates:
        params.append(tarea_id)
        conn.execute(f'UPDATE tareas SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
    conn.close()
    return obtener_tarea(tarea_id)

def eliminar_tarea(tarea_id: int):
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM tareas WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

# ESTADÍSTICAS
def obtener_resumen_proyecto(proyecto_id: int):
    conn = get_db_connection()
    proyecto = obtener_proyecto(proyecto_id)
    if not proyecto:
        conn.close()
        return None
    estados = conn.execute('SELECT estado, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY estado',
                          (proyecto_id,)).fetchall()
    prioridades = conn.execute('SELECT prioridad, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY prioridad',
                              (proyecto_id,)).fetchall()
    conn.close()
    return {
        'proyecto_id': proyecto_id,
        'proyecto_nombre': proyecto['nombre'],
        'total_tareas': proyecto['total_tareas'],
        'por_estado': {e['estado']: e['cantidad'] for e in estados},
        'por_prioridad': {p['prioridad']: p['cantidad'] for p in prioridades}
    }

def obtener_resumen_general():
    conn = get_db_connection()
    total_proyectos = conn.execute('SELECT COUNT(*) as total FROM proyectos').fetchone()['total']
    total_tareas = conn.execute('SELECT COUNT(*) as total FROM tareas').fetchone()['total']
    estados = conn.execute('SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado').fetchall()
    proyecto_top = conn.execute(
        'SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas FROM proyectos p LEFT JOIN tareas t ON p.id = t.proyecto_id GROUP BY p.id ORDER BY cantidad_tareas DESC LIMIT 1'
    ).fetchone()
    conn.close()
    proyecto_con_mas = None
    if proyecto_top and proyecto_top['cantidad_tareas'] > 0:
        proyecto_con_mas = {
            'id': proyecto_top['id'],
            'nombre': proyecto_top['nombre'],
            'cantidad_tareas': proyecto_top['cantidad_tareas']
        }
    return {
        'total_proyectos': total_proyectos,
        'total_tareas': total_tareas,
        'tareas_por_estado': {e['estado']: e['cantidad'] for e in estados},
        'proyecto_con_mas_tareas': proyecto_con_mas
    }