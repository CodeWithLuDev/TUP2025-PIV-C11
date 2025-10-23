from fastapi import FastAPI, HTTPException, Depends, Query
from typing import Annotated, Optional, List
import sqlite3
from sqlite3 import Connection
from datetime import datetime
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator

# ------------------------
# Constantes y DB
# ------------------------
DB_PATH = "tareas.db"
ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}
ALLOWED_PRIORIDADES = {"baja", "media", "alta"}

app = FastAPI(title="TP3 - API de Tareas Persistente")

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT,
            CHECK (estado IN ('pendiente', 'en_progreso', 'completada')),
            CHECK (prioridad IN ('baja','media','alta'))
        );
        """
    )
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Dependency para endpoints
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# -----------------------
# Pydantic models (v2)
# -----------------------
class TareaBase(BaseModel):
    descripcion: Annotated[Optional[str], Field(example="Comprar leche")] = None
    estado: Annotated[Optional[str], Field(example="pendiente")] = None
    prioridad: Annotated[Optional[str], Field(example="media")] = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ALLOWED_ESTADOS:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(ALLOWED_ESTADOS)}")
        return v

    @field_validator("prioridad")
    @classmethod
    def prioridad_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ALLOWED_PRIORIDADES:
            raise ValueError(f"Prioridad inválida. Debe ser una de: {', '.join(ALLOWED_PRIORIDADES)}")
        return v


class TareaCreate(TareaBase):
    descripcion: Annotated[str, Field(..., example="Comprar leche")]
    estado: Annotated[str, Field(..., example="pendiente")]
    prioridad: Annotated[str, Field(default="media")]


class TareaUpdate(TareaBase):
    pass


class TareaOut(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: Optional[str]

# ------------------------
# Utils
# ------------------------
def row_to_tarea(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "fecha_creacion": row["fecha_creacion"],
    }

# ------------------------
# Endpoints
# ------------------------
@app.get("/tareas", response_model=List[TareaOut])
def listar_tareas(
    estado: Optional[str] = Query(None, description="Filtro por estado"),
    texto: Optional[str] = Query(None, description="Buscar texto en la descripción"),
    prioridad: Optional[str] = Query(None, description="Filtro por prioridad"),
    orden: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="asc o desc por fecha_creacion"),
    db: Connection = Depends(get_db),
):
    query = "SELECT * FROM tareas"
    where_clauses = []
    params = []

    if estado:
        if estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {estado}")
        where_clauses.append("estado = ?")
        params.append(estado)

    if prioridad:
        if prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=400, detail=f"Prioridad inválida: {prioridad}")
        where_clauses.append("prioridad = ?")
        params.append(prioridad)

    if texto:
        where_clauses.append("descripcion LIKE ?")
        params.append(f"%{texto}%")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    orden_sql = "ASC" if (orden or "asc").lower() == "asc" else "DESC"
    query += f" ORDER BY datetime(fecha_creacion) {orden_sql}"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    return [row_to_tarea(r) for r in rows]

@app.post("/tareas", response_model=TareaOut, status_code=201)
def crear_tarea(tarea: TareaCreate, db: Connection = Depends(get_db)):
    ahora = datetime.now().isoformat()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, ahora),
    )
    db.commit()
    tarea_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    return row_to_tarea(row)

@app.put("/tareas/{tarea_id}", response_model=TareaOut)
def actualizar_tarea(tarea_id: int, datos: TareaUpdate, db: Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    updates = []
    params = []

    if datos.descripcion is not None:
        desc = datos.descripcion.strip()
        if not desc:
            raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
        updates.append("descripcion = ?")
        params.append(desc)

    if datos.estado is not None:
        if datos.estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=400, detail="Estado inválido")
        updates.append("estado = ?")
        params.append(datos.estado)

    if datos.prioridad is not None:
        if datos.prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=400, detail="Prioridad inválida")
        updates.append("prioridad = ?")
        params.append(datos.prioridad)

    if not updates:
        return row_to_tarea(row)

    params.append(tarea_id)
    sql = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
    cur.execute(sql, params)
    db.commit()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    updated = cur.fetchone()
    return row_to_tarea(updated)

@app.delete("/tareas/{tarea_id}", status_code=204)
def eliminar_tarea(tarea_id: int, db: Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    db.commit()
    return None

@app.get("/tareas/resumen")
def resumen_tareas(db: Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT estado, COUNT(*) AS cantidad FROM tareas GROUP BY estado")
    rows = cur.fetchall()
    resumen = {estado: 0 for estado in ALLOWED_ESTADOS}
    for r in rows:
        resumen[r["estado"]] = r["cantidad"]
    return resumen

@app.get("/")
def root():
    return {"mensaje": "API de Tareas (TP3) — usa /tareas"}
