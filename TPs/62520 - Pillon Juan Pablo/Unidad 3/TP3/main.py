from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from starlette.responses import RedirectResponse
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "tareas.db")
DB_NAME = DB_PATH

ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}
ALLOWED_PRIORIDADES = {"baja", "media", "alta"}

app = FastAPI(title="API Tareas - TP3 (SQLite)")

@app.get("/")
def root():
    return {"nombre": "API Tareas", "endpoints": ["/tareas", "/tareas/resumen", "/docs"]}

def get_conn():
    # check_same_thread=False para evitar problemas con TestClient/threads
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL,
        prioridad TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

class TareaBase(BaseModel):
    descripcion: str = Field(..., example="Comprar leche")
    estado: Optional[str] = Field("pendiente", example="pendiente")
    prioridad: Optional[str] = Field("media", example="media")

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError("la descripcion no puede estar vacía")
        return v.strip()

    @validator("estado")
    def estado_valido(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_ESTADOS:
            raise ValueError(f"estado debe ser uno de: {', '.join(ALLOWED_ESTADOS)}")
        return v

    @validator("prioridad")
    def prioridad_valida(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_PRIORIDADES:
            raise ValueError(f"prioridad debe ser uno de: {', '.join(ALLOWED_PRIORIDADES)}")
        return v

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError("la descripcion no puede estar vacía")
        return v.strip() if v is not None else v

    @validator("estado")
    def estado_valido(cls, v):
        if v is not None and v not in ALLOWED_ESTADOS:
            raise ValueError(f"estado debe ser uno de: {', '.join(ALLOWED_ESTADOS)}")
        return v

    @validator("prioridad")
    def prioridad_valida(cls, v):
        if v is not None and v not in ALLOWED_PRIORIDADES:
            raise ValueError(f"prioridad debe ser uno de: {', '.join(ALLOWED_PRIORIDADES)}")
        return v

@app.get("/tareas", response_model=List[Dict])
def listar_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    sql = "SELECT * FROM tareas"
    condiciones = []
    params: List[Any] = []

    if estado:
        condiciones.append("estado = ?")
        params.append(estado)
    if prioridad:
        condiciones.append("prioridad = ?")
        params.append(prioridad)
    if texto:
        condiciones.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{texto.lower()}%")

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)

    orden = (orden or "asc").lower()
    if orden not in ("asc", "desc"):
        orden = "asc"
    sql += f" ORDER BY fecha_creacion {orden.upper()}"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    fecha = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado or "pendiente", fecha, tarea.prioridad or "media")
    )
    conn.commit()
    tarea_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

# ruta sin parámetro debe registrarse antes de la ruta con parámetro
@app.put("/tareas/completar_todas")
def completar_todas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tareas SET estado = 'completada' WHERE estado != 'completada'")
    conn.commit()
    afectados = cur.rowcount
    conn.close()
    return {"mensaje": f"{afectados} tareas marcadas como completadas"}

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, datos: TareaUpdate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    existente = cur.fetchone()
    if not existente:
        conn.close()
        # devolver detail como dict para facilitar aserciones en tests
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    campos = []
    params: List[Any] = []
    if datos.descripcion is not None:
        campos.append("descripcion = ?")
        params.append(datos.descripcion)
    if datos.estado is not None:
        campos.append("estado = ?")
        params.append(datos.estado)
    if datos.prioridad is not None:
        campos.append("prioridad = ?")
        params.append(datos.prioridad)

    if campos:
        params.append(tarea_id)
        sql = "UPDATE tareas SET " + ", ".join(campos) + " WHERE id = ?"
        cur.execute(sql, params)
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    afectados = cur.rowcount
    conn.close()
    if afectados == 0:
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    return {"mensaje": "Tarea eliminada"}

@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM tareas")
    fila_total = cur.fetchone()
    total = fila_total["total"] if fila_total is not None else 0

    cur.execute("SELECT estado, COUNT(*) as total FROM tareas GROUP BY estado")
    rows_estado = cur.fetchall()
    por_estado = {e: 0 for e in ALLOWED_ESTADOS}
    for r in rows_estado:
        por_estado[r["estado"]] = r["total"]

    cur.execute("SELECT prioridad, COUNT(*) as total FROM tareas GROUP BY prioridad")
    rows_prio = cur.fetchall()
    por_prioridad = {p: 0 for p in ALLOWED_PRIORIDADES}
    for r in rows_prio:
        por_prioridad[r["prioridad"]] = r["total"]

    conn.close()
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

# aliases para rutas comunes que pediste en logs
@app.get("/resumen")
def resumen_alias():
    return resumen_tareas()

@app.get("/documentos")
def documentos_alias():
    return RedirectResponse(url="/docs")