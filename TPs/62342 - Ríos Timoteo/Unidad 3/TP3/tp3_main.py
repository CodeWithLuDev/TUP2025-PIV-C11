# tp3_main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
import sqlite3
from typing import Optional, List
from datetime import datetime
import os

DB_NAME = "tareas.db"

app = FastAPI(title="TP3 - API de Tareas Persistente")

# ==================== MODELOS ====================

ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta"]

class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"

    @validator("estado")
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido: {v}")
        return v

    @validator("prioridad")
    def validar_prioridad(cls, v):
        if v not in PRIORIDADES_VALIDAS:
            raise ValueError(f"Prioridad inválida: {v}")
        return v

# ==================== DB ====================

def init_db():
    """Crea la base de datos y la tabla tareas si no existen"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT,
            prioridad TEXT
        )
    """)
    conn.commit()
    conn.close()

# ==================== HELPERS ====================

def ejecutar(query: str, params=(), fetch=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        result = cursor.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

# ==================== ENDPOINTS ====================

@app.get("/")
def raiz():
    return {"mensaje": "API de Tareas TP3", "endpoints": ["/tareas", "/tareas/resumen"]}

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc")
):
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    if estado:
        query += " AND estado=?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad=?"
        params.append(prioridad)
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    filas = ejecutar(query, tuple(params), fetch=True)
    return [
        {"id": f[0], "descripcion": f[1], "estado": f[2], "fecha_creacion": f[3], "prioridad": f[4]}
        for f in filas
    ]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    fecha = datetime.now().isoformat()
    try:
        ejecutar(
            "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
            (tarea.descripcion.strip(), tarea.estado, fecha, tarea.prioridad)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    tarea_id = ejecutar("SELECT last_insert_rowid()", fetch=True)[0][0]
    return {"id": tarea_id, "descripcion": tarea.descripcion.strip(), "estado": tarea.estado, "fecha_creacion": fecha, "prioridad": tarea.prioridad}

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: Tarea):
    filas = ejecutar("SELECT * FROM tareas WHERE id=?", (tarea_id,), fetch=True)
    if not filas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    fecha = filas[0][3]  # mantener fecha original
    ejecutar(
        "UPDATE tareas SET descripcion=?, estado=?, prioridad=? WHERE id=?",
        (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, tarea_id)
    )
    return {"id": tarea_id, "descripcion": tarea.descripcion.strip(), "estado": tarea.estado, "fecha_creacion": fecha, "prioridad": tarea.prioridad}

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    filas = ejecutar("SELECT * FROM tareas WHERE id=?", (tarea_id,), fetch=True)
    if not filas:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ejecutar("DELETE FROM tareas WHERE id=?", (tarea_id,))
    return {"mensaje": f"Tarea {tarea_id} eliminada"}

@app.get("/tareas/resumen")
def resumen():
    filas = ejecutar("SELECT estado, COUNT(*) FROM tareas GROUP BY estado", fetch=True)
    resumen_estado = {estado: 0 for estado in ESTADOS_VALIDOS}
    for e, c in filas:
        resumen_estado[e] = c
    filas = ejecutar("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad", fetch=True)
    resumen_prioridad = {p: 0 for p in PRIORIDADES_VALIDAS}
    for p, c in filas:
        resumen_prioridad[p] = c
    total = ejecutar("SELECT COUNT(*) FROM tareas", fetch=True)[0][0]
    return {"total_tareas": total, "por_estado": resumen_estado, "por_prioridad": resumen_prioridad}

@app.put("/tareas/completar_todas")
def completar_todas():
    ejecutar("UPDATE tareas SET estado='completada'")
    return {"mensaje": "Todas las tareas fueron completadas"}

# ==================== INICIALIZACIÓN DB ====================
if not os.path.exists(DB_NAME):
    init_db()

# test_tp3.py
import pytest
from fastapi.testclient import TestClient
from tp3_main import app, init_db, DB_NAME
import os

client = TestClient(app)

# ==================== FIXTURE ====================
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Se ejecuta antes y después de cada test"""
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
    yield
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

# ==================== GET /tareas ====================
def test_01_listar_vacio():
    res = client.get("/tareas")
    assert res.status_code == 200
    assert res.json() == []

def test_02_listar_todas():
    client.post("/tareas", json={"descripcion": "Tarea 1"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    res = client.get("/tareas")
    assert res.status_code == 200
    assert len(res.json()) == 2

def test_03_filtrar_por_estado():
    client.post("/tareas", json={"descripcion": "Pendiente", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Completada", "estado": "completada"})
    res = client.get("/tareas?estado=pendiente")
    tareas = res.json()
    assert len(tareas) == 1
    assert tareas[0]["estado"] == "pendiente"

def test_04_filtrar_por_texto():
    client.post("/tareas", json={"descripcion": "Comprar leche"})
    client.post("/tareas", json={"descripcion": "Estudiar matemáticas"})
    res = client.get("/tareas?texto=leche")
    tareas = res.json()
    assert len(tareas) == 1
    assert "leche" in tareas[0]["descripcion"].lower()

def test_05_filtrar_por_prioridad():
    client.post("/tareas", json={"descripcion": "Alta", "prioridad": "alta"})
    client.post("/tareas", json={"descripcion": "Baja", "prioridad": "baja"})
    res = client.get("/tareas?prioridad=alta")
    tareas = res.json()
    assert len(tareas) == 1
    assert tareas[0]["prioridad"] == "alta"

# ==================== POST /tareas ====================
def test_06_crear_valida():
    res = client.post("/tareas", json={"descripcion": "Hacer deberes"})
    assert res.status_code == 201
    data = res.json()
    assert data["descripcion"] == "Hacer deberes"
    assert data["estado"] == "pendiente"

def test_07_crear_vacia():
    res = client.post("/tareas", json={"descripcion": ""})
    assert res.status_code == 422

def test_08_crear_espacios():
    res = client.post("/tareas", json={"descripcion": "   "})
    assert res.status_code == 422

def test_09_crear_estado_invalido():
    res = client.post("/tareas", json={"descripcion": "Tarea", "estado": "error"})
    assert res.status_code == 422

def test_10_crear_sin_estado():
    res = client.post("/tareas", json={"descripcion": "Sin estado"})
    assert res.status_code == 201
    assert res.json()["estado"] == "pendiente"

# ==================== PUT /tareas/{id} ====================
def test_11_editar_existente():
    crear = client.post("/tareas", json={"descripcion": "Original"})
    tid = crear.json()["id"]
    res = client.put(f"/tareas/{tid}", json={"descripcion": "Editada", "estado": "completada", "prioridad": "alta"})
    data = res.json()
    assert res.status_code == 200
    assert data["descripcion"] == "Editada"
    assert data["estado"] == "completada"
    assert data["prioridad"] == "alta"

def test_12_editar_inexistente():
    res = client.put("/tareas/999", json={"descripcion": "Nada"})
    assert res.status_code == 404

def test_13_editar_solo_estado():
    crear = client.post("/tareas", json={"descripcion": "Tarea test"})
    tid = crear.json()["id"]
    res = client.put(f"/tareas/{tid}", json={"estado": "en_progreso"})
    data = res.json()
    assert res.status_code == 200
    assert data["estado"] == "en_progreso"
    assert data["descripcion"] == "Tarea test"

# ==================== DELETE /tareas/{id} ====================
def test_14_eliminar_existente():
    crear = client.post("/tareas", json={"descripcion": "A eliminar"})
    tid = crear.json()["id"]
    res = client.delete(f"/tareas/{tid}")
    assert res.status_code == 200
    assert "mensaje" in res.json()
    res2 = client.get("/tareas")
    assert len(res2.json()) == 0

def test_15_eliminar_inexistente():
    res = client.delete("/tareas/999")
    assert res.status_code == 404

# ==================== GET /tareas/resumen ====================
def test_16_resumen_con_tareas():
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada"})
    res = client.get("/tareas/resumen")
    data = res.json()
    assert res.status_code == 200
    assert data["por_estado"]["pendiente"] == 1
    assert data["por_estado"]["en_progreso"] == 1
    assert data["por_estado"]["completada"] == 1

# ==================== PUT /tareas/completar_todas ====================
def test_17_completar_todas_las_tareas():
    client.post("/tareas", json={"descripcion": "T1"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    res = client.put("/tareas/completar_todas")
    assert res.status_code == 200
    assert "mensaje" in res.json()
    tareas = client.get("/tareas").json()
    for t in tareas:
        assert t["estado"] == "completada"

# ==================== GET / ====================
def test_18_endpoint_raiz():
    res = client.get("/")
    assert res.status_code == 200
    assert "mensaje" in res.json()

