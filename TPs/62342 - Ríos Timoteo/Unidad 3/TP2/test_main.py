import pytest
from fastapi.testclient import TestClient
from main import app, tareas_db, ultimo_id

client = TestClient(app)

# Limpiar la base de datos antes de cada test
@pytest.fixture(autouse=True)
def reset_db():
    tareas_db.clear()
    global ultimo_id
    ultimo_id = 1

# ==================== TESTS GET /tareas ====================

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
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["estado"] == "pendiente"

def test_04_filtrar_por_texto():
    client.post("/tareas", json={"descripcion": "Comprar leche"})
    client.post("/tareas", json={"descripcion": "Estudiar matemáticas"})
    res = client.get("/tareas?texto=leche")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert "leche" in res.json()[0]["descripcion"].lower()

# ==================== TESTS POST /tareas ====================

def test_05_crear_valida():
    res = client.post("/tareas", json={"descripcion": "Hacer deberes"})
    assert res.status_code == 201
    data = res.json()
    assert data["descripcion"] == "Hacer deberes"
    assert data["estado"] == "pendiente"

def test_06_crear_vacia():
    res = client.post("/tareas", json={"descripcion": ""})
    assert res.status_code == 422

def test_07_crear_espacios():
    res = client.post("/tareas", json={"descripcion": "   "})
    assert res.status_code == 422

def test_08_crear_estado_invalido():
    res = client.post("/tareas", json={"descripcion": "Tarea", "estado": "error"})
    assert res.status_code == 400

def test_09_crear_sin_estado():
    res = client.post("/tareas", json={"descripcion": "Sin estado"})
    assert res.status_code == 201
    assert res.json()["estado"] == "pendiente"

# ==================== TESTS PUT /tareas/{id} ====================

def test_10_editar_existente():
    crear = client.post("/tareas", json={"descripcion": "Original"})
    tid = crear.json()["id"]
    res = client.put(f"/tareas/{tid}", json={"descripcion": "Editada", "estado": "completada"})
    assert res.status_code == 200
    data = res.json()
    assert data["descripcion"] == "Editada"
    assert data["estado"] == "completada"

def test_11_editar_inexistente():
    res = client.put("/tareas/999", json={"descripcion": "Nada"})
    assert res.status_code == 404

def test_12_editar_solo_estado():
    crear = client.post("/tareas", json={"descripcion": "Tarea test"})
    tid = crear.json()["id"]
    res = client.put(f"/tareas/{tid}", json={"estado": "en_progreso"})
    assert res.status_code == 200
    data = res.json()
    assert data["estado"] == "en_progreso"
    assert data["descripcion"] == "Tarea test"

# ==================== TESTS DELETE /tareas/{id} ====================

def test_13_eliminar_existente():
    crear = client.post("/tareas", json={"descripcion": "A eliminar"})
    tid = crear.json()["id"]
    res = client.delete(f"/tareas/{tid}")
    assert res.status_code == 200
    assert "mensaje" in res.json()
    res2 = client.get("/tareas")
    assert len(res2.json()) == 0

def test_14_eliminar_inexistente():
    res = client.delete("/tareas/999")
    assert res.status_code == 404

# ==================== TESTS GET /tareas/resumen ====================

def test_15_resumen_con_tareas():
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada"})
    res = client.get("/tareas/resumen")
    data = res.json()
    assert res.status_code == 200
    assert data["pendiente"] == 1
    assert data["en_progreso"] == 1
    assert data["completada"] == 1

def test_16_resumen_sin_tareas():
    res = client.get("/tareas/resumen")
    data = res.json()
    assert res.status_code == 200
    assert data["pendiente"] == 0
    assert data["en_progreso"] == 0
    assert data["completada"] == 0

# ==================== TESTS POST /tareas/completar_todas ====================

def test_17_completar_todas_las_tareas():
    client.post("/tareas", json={"descripcion": "T1"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    res = client.post("/tareas/completar_todas")
    assert res.status_code == 200
    assert "mensaje" in res.json()
    tareas = client.get("/tareas").json()
    for t in tareas:
        assert t["estado"] == "completada"

def test_18_completar_todas_sin_tareas():
    res = client.post("/tareas/completar_todas")
    assert res.status_code == 200
    assert "Todas las tareas fueron completadas" in res.json()["mensaje"]

