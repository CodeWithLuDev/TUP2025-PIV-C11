from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3
from pathlib import Path as FSPath
DB_PATH = "tareas.db"

app = FastAPI(title="Mini API de Tareas - TP3 (SQLite)")



def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    FSPath(DB_PATH).touch(exist_ok=True)
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_creacion TEXT,
                prioridad TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

def fila_a_dict(fila):
    if not fila:
        return None
    return {
        "id": fila[0],
        "descripcion": fila[1],
        "estado": fila[2],
        "fecha_creacion": fila[3],
        "prioridad": fila[4],
    }

init_db()

ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}  
ALLOWED_PRIORIDADES = {"baja", "media", "alta"}

    




class TareaBase(BaseModel):
    descripcion: str = Field(..., description="Descripción de la tarea")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(
        default="pendiente", description="Estado actual de la tarea"
    )
    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(
        default="media", description="Prioridad de la tarea"
    )

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(default=None, description="Nueva descripción")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(
        default=None, description="Nuevo estado"
    )

    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(default=None, description="Nueva prioridad")


    @field_validator("descripcion")
    @classmethod
    def validar_desc_update(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v



def error(status: int, msg: str):
    return JSONResponse(status_code=status, content={"error": msg})

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(default=None),
    texto: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default=None, description="asc o desc"),
):
    # --- Validaciones de filtros (igual filosofía que TP2) ---
    if estado is not None and estado not in ALLOWED_ESTADOS:
        raise HTTPException(status_code=400, detail="Estado inválido. Use: pendiente, en_progreso, completada.")

    if prioridad is not None:
        if prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=400, detail="Prioridad inválida. Use: baja, media, alta.")

    if orden is not None:
        orden_limpio = orden.lower()
        if orden_limpio not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="Orden inválido. Use: asc o desc.")
    else:
        orden_limpio = None

    # --- Construcción de la consulta dinámica y parámetros ---
    sql = """
        SELECT id, descripcion, estado, fecha_creacion, prioridad
        FROM tareas
    """
    where = []
    params = []

    if estado is not None:
        where.append("estado = ?")
        params.append(estado)

    if texto is not None:
        where.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{texto.lower()}%")

    if prioridad is not None:
        where.append("prioridad = ?")
        params.append(prioridad)

    if where:
        sql += " WHERE " + " AND ".join(where)

    # Orden por fecha_creacion (texto ISO); usamos datetime() para ordenar correctamente
    if orden_limpio:
        sql += f" ORDER BY datetime(fecha_creacion) {orden_limpio.upper()}"

    conn = get_connection()
    try:
        cur = conn.cursor()
        filas = cur.execute(sql, params).fetchall()
        resultado = [
            {
                "id": f[0],
                "descripcion": f[1],
                "estado": f[2],
                "fecha_creacion": f[3],
                "prioridad": f[4],
            }
            for f in filas
        ]
        return resultado
    finally:
        conn.close()

@app.get("/tareas/{id}")
def obtener_tarea_por_id(id: int = Path(..., ge=1)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        fila = cur.execute(
            "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE id = ?",
            (id,),
        ).fetchone()

        if fila is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada.")

        return fila_a_dict(fila)

    finally:
        conn.close()



@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaBase):
    descripcion = (tarea.descripcion or "").strip()
    if not descripcion:
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía.")
    
    if tarea.estado not in ALLOWED_ESTADOS:
        raise HTTPException(status_code=400, detail="Estado inválido. Use: pendiente, en_progreso, completada.")
    
    prioridad = tarea.prioridad or "media"
    if prioridad not in ALLOWED_PRIORIDADES:
        raise HTTPException(status_code=400, detail="Prioridad inválida. Use: baja, media, alta.")
    
    fecha_creacion = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
            VALUES (?, ?, ?, ?)
            """,
            (descripcion, tarea.estado, fecha_creacion, prioridad),
        )
        conn.commit()
        nuevo_id = cur.lastrowid

        fila = cur.execute(
            "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE id = ?",
            (nuevo_id,),
        ).fetchone()

        return fila_a_dict(fila)
    
    finally:
        conn.close()


@app.put("/tareas/{tarea_id}")
def actualizar_tarea(
    body: TareaUpdate,
    tarea_id: int = Path(..., ge=1, description="ID de la tarea a modificar")
):
    # 1) Construir dinámicamente el SET y validar campos opcionales
    set_clauses = []
    params = []

    if body.descripcion is not None:
        desc = body.descripcion.strip()
        if not desc:
            raise HTTPException(status_code=400, detail="La descripción no puede estar vacía.")
        set_clauses.append("descripcion = ?")
        params.append(desc)

    if body.estado is not None:
        if body.estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=400, detail="Estado inválido. Use: pendiente, en_progreso, completada.")
        set_clauses.append("estado = ?")
        params.append(body.estado)

    if body.prioridad is not None:
        if body.prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=400, detail="Prioridad inválida. Use: baja, media, alta.")
        set_clauses.append("prioridad = ?")
        params.append(body.prioridad)

    if not set_clauses:
        # Nada para actualizar
        return error(400, "No se enviaron campos para actualizar")

    # 2) Ejecutar UPDATE y verificar existencia del id
    sql = f"UPDATE tareas SET {', '.join(set_clauses)} WHERE id = ?"
    params.append(tarea_id)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()

        if cur.rowcount == 0:
            # No existe la tarea con ese id
            raise HTTPException(status_code=404, detail="error: La tarea no existe")

        # 3) Devolver la tarea actualizada
        fila = cur.execute(
            "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE id = ?",
            (tarea_id,),
        ).fetchone()

        return fila_a_dict(fila)

    finally:
        conn.close()

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(
    tarea_id: int = Path(..., ge=1, description="ID de la tarea a eliminar")
):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()

        if cur.rowcount == 0:
            # No existía una tarea con ese id
            raise HTTPException(status_code=404, detail="error: La tarea no existe")

        # Mantengo mismo “shape” de respuesta que venías usando (200 con mensaje)
        return {"mensaje": "Tarea eliminada", "id": tarea_id}
        # Si tus tests esperaran 204 sin cuerpo, usar:
        # from fastapi import Response
        # return Response(status_code=204)
    finally:
        conn.close()


@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_connection()
    try:
        cur = conn.cursor()
        filas = cur.execute(
            "SELECT estado, COUNT(*) FROM tareas GROUP BY estado"
        ).fetchall()

        # Aseguramos todas las claves aunque no haya filas de ese estado
        resumen = {estado: 0 for estado in ALLOWED_ESTADOS}
        for estado, cantidad in filas:
            if estado in resumen:
                resumen[estado] = cantidad

        return resumen
    finally:
        conn.close()
