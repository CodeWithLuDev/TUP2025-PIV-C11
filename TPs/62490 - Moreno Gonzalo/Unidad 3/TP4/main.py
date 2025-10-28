from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from typing import Optional, List

# Importar desde archivos separados
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse
)
from database import init_db, get_db_connection, row_to_dict, DB_NAME

# Exportar para compatibilidad con tests
__all__ = ['app', 'init_db', 'DB_NAME']

# ============== CONFIGURACIÓN DE FASTAPI ==============

app = FastAPI(
    title="API de Proyectos y Tareas",
    description="API con relaciones entre tablas - TP4",
    version="3.0.0"
)

# ============== STARTUP ==============

@app.on_event("startup")
def startup_event():
    """Inicializa la base de datos al arrancar la aplicación"""
    init_db()

# ============== ENDPOINTS RAÍZ ==============

@app.get("/")
def root():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "API de Proyectos y Tareas - TP4",
        "version": "3.0.0",
        "endpoints": {
            "proyectos": [
                "GET /proyectos",
                "POST /proyectos",
                "GET /proyectos/{id}",
                "PUT /proyectos/{id}",
                "DELETE /proyectos/{id}",
                "GET /proyectos/{id}/tareas",
                "POST /proyectos/{id}/tareas",
                "GET /proyectos/{id}/resumen"
            ],
            "tareas": [
                "GET /tareas",
                "PUT /tareas/{id}",
                "DELETE /tareas/{id}"
            ],
            "resumen": [
                "GET /resumen"
            ]
        }
    }

# ============== ENDPOINTS DE PROYECTOS ==============

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crear un nuevo proyecto"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar nombre duplicado
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Ya existe un proyecto con ese nombre"
            )
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
        
        proyecto_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        nuevo_proyecto = row_to_dict(cursor.fetchone())
        nuevo_proyecto["total_tareas"] = 0
        
        return nuevo_proyecto

@app.get("/proyectos", response_model=List[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None, description="Filtrar por nombre")):
    """Listar todos los proyectos con filtro opcional por nombre"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if nombre:
            cursor.execute("""
                SELECT p.*, COUNT(t.id) as total_tareas
                FROM proyectos p
                LEFT JOIN tareas t ON p.id = t.proyecto_id
                WHERE p.nombre LIKE ?
                GROUP BY p.id
            """, (f"%{nombre}%",))
        else:
            cursor.execute("""
                SELECT p.*, COUNT(t.id) as total_tareas
                FROM proyectos p
                LEFT JOIN tareas t ON p.id = t.proyecto_id
                GROUP BY p.id
            """)
        
        proyectos = [row_to_dict(row) for row in cursor.fetchall()]
        return proyectos

@app.get("/proyectos/{id}", response_model=ProyectoResponse)
def obtener_proyecto(id: int):
    """Obtener un proyecto específico con contador de tareas"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (id,))
        
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return row_to_dict(proyecto)

@app.put("/proyectos/{id}", response_model=ProyectoResponse)
def actualizar_proyecto(id: int, proyecto_update: ProyectoUpdate):
    """Actualizar un proyecto existente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Verificar nombre duplicado si se está cambiando
        if proyecto_update.nombre:
            cursor.execute(
                "SELECT id FROM proyectos WHERE nombre = ? AND id != ?",
                (proyecto_update.nombre, id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
        
        # Actualizar campos
        campos = []
        valores = []
        
        if proyecto_update.nombre is not None:
            campos.append("nombre = ?")
            valores.append(proyecto_update.nombre)
        
        if proyecto_update.descripcion is not None:
            campos.append("descripcion = ?")
            valores.append(proyecto_update.descripcion)
        
        if campos:
            valores.append(id)
            query = f"UPDATE proyectos SET {', '.join(campos)} WHERE id = ?"
            cursor.execute(query, valores)
        
        # Obtener proyecto actualizado
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (id,))
        
        return row_to_dict(cursor.fetchone())

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    """Eliminar un proyecto y sus tareas (CASCADE)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Contar tareas antes de eliminar
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
        tareas_eliminadas = cursor.fetchone()["total"]
        
        # Eliminar proyecto (CASCADE eliminará las tareas)
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
        
        return {
            "mensaje": "Proyecto eliminado exitosamente",
            "tareas_eliminadas": tareas_eliminadas
        }

# ============== ENDPOINTS DE TAREAS ==============

@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """Crear una tarea dentro de un proyecto"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="El proyecto no existe")
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
            VALUES (?, ?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion))
        
        tarea_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        nueva_tarea = row_to_dict(cursor.fetchone())
        
        return nueva_tarea

@app.get("/proyectos/{id}/tareas", response_model=List[TareaResponse])
def listar_tareas_de_proyecto(id: int):
    """Listar todas las tareas de un proyecto específico"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        cursor.execute("""
            SELECT * FROM tareas WHERE proyecto_id = ?
            ORDER BY id ASC
        """, (id,))
        
        tareas = [row_to_dict(tarea) for tarea in cursor.fetchall()]
        return tareas

@app.get("/tareas", response_model=List[TareaResponse])
def listar_todas_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: Optional[str] = Query(None, description="Ordenar: 'asc' o 'desc'")
):
    """Listar todas las tareas con filtros opcionales"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado)
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        if proyecto_id:
            query += " AND proyecto_id = ?"
            params.append(proyecto_id)
        
        # Ordenamiento
        if orden and orden.lower() in ['asc', 'desc']:
            query += f" ORDER BY fecha_creacion {orden.upper()}"
        else:
            query += " ORDER BY id ASC"
        
        cursor.execute(query, params)
        tareas = [row_to_dict(tarea) for tarea in cursor.fetchall()]
        
        return tareas

@app.put("/tareas/{id}", response_model=TareaResponse)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """Actualizar una tarea existente"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Si se está cambiando de proyecto, verificar que existe
        if tarea_update.proyecto_id:
            cursor.execute("SELECT id FROM proyectos WHERE id = ?", (tarea_update.proyecto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="El proyecto destino no existe")
        
        # Actualizar campos
        campos = []
        valores = []
        
        if tarea_update.descripcion is not None:
            campos.append("descripcion = ?")
            valores.append(tarea_update.descripcion)
        
        if tarea_update.estado is not None:
            campos.append("estado = ?")
            valores.append(tarea_update.estado)
        
        if tarea_update.prioridad is not None:
            campos.append("prioridad = ?")
            valores.append(tarea_update.prioridad)
        
        if tarea_update.proyecto_id is not None:
            campos.append("proyecto_id = ?")
            valores.append(tarea_update.proyecto_id)
        
        if campos:
            valores.append(id)
            query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
            cursor.execute(query, valores)
        
        # Obtener tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        return row_to_dict(cursor.fetchone())

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Eliminar una tarea"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        
        return {"mensaje": "Tarea eliminada exitosamente"}

# ============== ENDPOINTS DE RESUMEN ==============

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    """Obtener resumen estadístico de un proyecto"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Contar total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
        total_tareas = cursor.fetchone()["total"]
        
        # Contar por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY estado
        """, (id,))
        
        por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            por_estado[row["estado"]] = row["cantidad"]
        
        # Contar por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY prioridad
        """, (id,))
        
        por_prioridad = {"baja": 0, "media": 0, "alta": 0}
        for row in cursor.fetchall():
            por_prioridad[row["prioridad"]] = row["cantidad"]
        
        return {
            "proyecto_id": id,
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/resumen")
def resumen_general():
    """Obtener resumen general de toda la aplicación"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total de proyectos
        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()["total"]
        
        # Total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Tareas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        
        tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            tareas_por_estado[row["estado"]] = row["cantidad"]
        
        # Proyecto con más tareas
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        
        proyecto_top = cursor.fetchone()
        
        proyecto_con_mas_tareas = None
        if proyecto_top and proyecto_top["cantidad_tareas"] > 0:
            proyecto_con_mas_tareas = {
                "id": proyecto_top["id"],
                "nombre": proyecto_top["nombre"],
                "cantidad_tareas": proyecto_top["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }