# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List, Dict, Any
import sqlite3
from datetime import datetime
import os

# --- DB en subcarpeta para minimizar locks en Windows ---
DB_DIR = "db"
os.makedirs(DB_DIR, exist_ok=True)

# El test importa DB_NAME, por eso exportamos la ruta completa:
DB_NAME = os.path.join(DB_DIR, "tareas.db")
DB_PATH = DB_NAME

ESTADOS = ("pendiente", "en_progreso", "completada")
PRIORIDADES = ("baja", "media", "alta")


def get_conn():
    # check_same_thread=False: evita problemas con TestClient/hilos en Windows
    # timeout: si hay lock corto, espera un poco antes de fallar
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5.0)
    return conn


def init_db():
    with get_conn() as conn:
        # Usar journal_mode=DELETE para no dejar -wal/-shm que traben borrados
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.commit()


app = FastAPI(title="API de Tareas Persistente (TP3)")

# ============ MODELOS ============
class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1)
    # Defaults para que el test pueda omitirlos
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"

    @validator("descripcion")
    def desc_no_vacia(cls, v: str):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía.")
        return v.strip()


class TareaCreate(TareaBase):
    pass


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None

    @validator("descripcion")
    def desc_no_vacia(cls, v: Optional[str]):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía.")
        return v.strip() if v is not None else v


class TareaOut(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]
    fecha_creacion: str


# ============ HELPERS ============
def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "fecha_creacion": row[4],
    }


# Importante: NO usamos startup; los tests llaman init_db() en su fixture.
# @app.on_event("startup")
# def on_startup():
#     init_db()


# ============ ENDPOINT RAÍZ ============
@app.get("/")
def raiz():
    return {
        "nombre": "API de Tareas Persistente (TP3)",
        "endpoints": ["/tareas", "/tareas/resumen", "/tareas/completar_todas"],
    }


# ============ LISTAR + FILTROS ============
@app.get("/tareas", response_model=List[TareaOut])
def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("asc"),
):
    clauses = []
    params: List[Any] = []
    if estado:
        clauses.append("estado = ?")
        params.append(estado)
    if prioridad:
        clauses.append("prioridad = ?")
        params.append(prioridad)
    if texto:
        clauses.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{texto.lower()}%")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order_sql = "ASC" if (orden or "asc") == "asc" else "DESC"

    query = f"""
        SELECT id, descripcion, estado, prioridad, fecha_creacion
        FROM tareas {where_sql}
        ORDER BY fecha_creacion {order_sql}
    """
    with get_conn() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
    return [row_to_dict(r) for r in rows]


# ============ RESUMEN ============
@app.get("/tareas/resumen")
def resumen():
    with get_conn() as conn:
        por_estado = {e: 0 for e in ESTADOS}
        for estado, cnt in conn.execute(
            "SELECT estado, COUNT(*) FROM tareas GROUP BY estado"
        ):
            por_estado[estado] = cnt

        por_prioridad = {p: 0 for p in PRIORIDADES}
        for prioridad, cnt in conn.execute(
            "SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad"
        ):
            por_prioridad[prioridad] = cnt

        total = conn.execute("SELECT COUNT(*) FROM tareas").fetchone()[0]

    return {
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
        "total_tareas": total,  # clave que espera el test
    }


# ============ CREAR ============
@app.post("/tareas", response_model=TareaOut, status_code=201)
def crear_tarea(tarea: TareaCreate):
    # microsegundos para ordenar bien con sleeps cortos de los tests
    ahora = datetime.now().isoformat(timespec="microseconds")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
            (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, ahora),
        )
        new_id = cur.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT id, descripcion, estado, prioridad, fecha_creacion FROM tareas WHERE id = ?",
            (new_id,),
        ).fetchone()
    return row_to_dict(row)


# ============ COMPLETAR TODAS ============
@app.put("/tareas/completar_todas")
def completar_todas():
    with get_conn() as conn:
        conn.execute("UPDATE tareas SET estado = 'completada'")
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM tareas").fetchone()[0]
    return {"mensaje": f"Se marcaron {total} tareas como completadas"}


# ============ ACTUALIZAR ============
@app.put("/tareas/{id:int}", response_model=TareaOut)
def actualizar_tarea(id: int, cambios: TareaUpdate):
    with get_conn() as conn:
        existe = conn.execute("SELECT id FROM tareas WHERE id = ?", (id,)).fetchone()
        if existe is None:
            # el test espera detail={"error": "..."}
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

        fields = []
        params: List[Any] = []
        if cambios.descripcion is not None:
            fields.append("descripcion = ?")
            params.append(cambios.descripcion.strip())
        if cambios.estado is not None:
            fields.append("estado = ?")
            params.append(cambios.estado)
        if cambios.prioridad is not None:
            fields.append("prioridad = ?")
            params.append(cambios.prioridad)

        if fields:
            params.append(id)
            conn.execute(f"UPDATE tareas SET {', '.join(fields)} WHERE id = ?", params)
            conn.commit()

        row = conn.execute(
            "SELECT id, descripcion, estado, prioridad, fecha_creacion FROM tareas WHERE id = ?",
            (id,),
        ).fetchone()
    return row_to_dict(row)


# ============ ELIMINAR ============
@app.delete("/tareas/{id:int}")
def borrar_tarea(id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
        conn.commit()
    # el test espera 200 + {"mensaje": "..."}
    return {"mensaje": "Tarea eliminada"}
