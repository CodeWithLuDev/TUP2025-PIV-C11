# test_TP2.py (Corregido)

import pytest
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def reset_db():
    main.tareas_db.clear()
    main.contador_id = 1
    yield

# --- Tests que ya pasaban (sin cambios) ---
def test_01_obtener_tareas_vacia():
    response = client.get("/tareas")
    assert response.status_code == 200
    assert response.json() == []

def test_02_obtener_todas_las_tareas():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "en_progreso"})
    response = client.get("/tareas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_03_crear_tarea_sin_descripcion():
    response = client.post("/tareas", json={"descripcion": "", "estado": "pendiente"})
    assert response.status_code == 422

def test_04_crear_tarea_estado_invalido():
    response = client.post("/tareas", json={"descripcion": "Test", "estado": "invalido"})
    assert response.status_code == 422

def test_05_crear_tarea_solo_descripcion():
    response = client.post("/tareas", json={"descripcion": "Nueva tarea"})
    assert response.status_code == 201
    data = response.json()
    assert data["descripcion"] == "Nueva tarea"
    assert data["estado"] == "pendiente"

def test_06_crear_tarea_descripcion_vacia():
    response = client.post("/tareas", json={"descripcion": "   ", "estado": "pendiente"})
    assert response.status_code == 422

def test_07_crear_tarea_exitosamente():
    response = client.post("/tareas", json={"descripcion": "Completar TP", "estado": "en_progreso"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1

def test_08_obtener_tarea_por_id():
    create_response = client.post("/tareas", json={"descripcion": "Test", "estado": "pendiente"})
    tarea_id = create_response.json()["id"]
    response = client.get(f"/tareas/{tarea_id}")
    assert response.status_code == 200
    assert response.json()["id"] == tarea_id

def test_09_obtener_tarea_id_inexistente():
    response = client.get("/tareas/999")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_10_actualizar_tarea_existente():
    create_response = client.post("/tareas", json={"descripcion": "Original", "estado": "pendiente"})
    tarea_id = create_response.json()["id"]
    response = client.put(f"/tareas/{tarea_id}", json={"descripcion": "Actualizada", "estado": "completada"})
    assert response.status_code == 200
    data = response.json()
    assert data["descripcion"] == "Actualizada"
    assert data["estado"] == "completada"

# --- Tests que fallaban (Ahora corregidos) ---

# Test 11: Actualizar tarea inexistente
def test_11_actualizar_tarea_inexistente():
    response = client.put("/tareas/999", json={
        "descripcion": "No existe",
        "estado": "pendiente"
    })
    assert response.status_code == 404
    # CORRECCIÓN: Ahora busco "error" dentro del diccionario "detail".
    assert "error" in response.json()["detail"]

# Test 12: Eliminar tarea existente (sin cambios)
def test_12_eliminar_tarea_existente():
    create_response = client.post("/tareas", json={"descripcion": "A eliminar", "estado": "pendiente"})
    tarea_id = create_response.json()["id"]
    response = client.delete(f"/tareas/{tarea_id}")
    assert response.status_code == 200
    assert "mensaje" in response.json()
    get_response = client.get(f"/tareas/{tarea_id}")
    assert get_response.status_code == 404

# Test 13: Eliminar tarea inexistente
def test_13_eliminar_tarea_inexistente():
    response = client.delete("/tareas/999")
    assert response.status_code == 404
    # CORRECCIÓN: Hago el mismo cambio aquí.
    assert "error" in response.json()["detail"]

# Test 14: Filtrar tareas por estado (sin cambios)
def test_14_filtrar_tareas_por_estado():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "pendiente"})
    response = client.get("/tareas?estado=pendiente")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(t["estado"] == "pendiente" for t in data)

# Test 15: Filtrar por estado inválido
def test_15_filtrar_estado_invalido():
    response = client.get("/tareas?estado=invalido")
    assert response.status_code == 400
    # CORRECCIÓN: Y el último cambio es aquí.
    assert "error" in response.json()["detail"]

# --- Resto de tests que ya pasaban (sin cambios) ---
def test_16_buscar_tareas_por_texto():
    client.post("/tareas", json={"descripcion": "Estudiar Python"})
    client.post("/tareas", json={"descripcion": "Repasar Python avanzado"})
    response = client.get("/tareas?texto=Python")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_17_obtener_resumen():
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "T3", "estado": "completada"})
    client.post("/tareas", json={"descripcion": "T4", "estado": "completada"})
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["pendiente"] == 1
    assert data["en_progreso"] == 1
    assert data["completada"] == 2

def test_18_resumen_sin_tareas():
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["pendiente"] == 0
    assert data["en_progreso"] == 0
    assert data["completada"] == 0

def test_19_completar_todas_las_tareas():
    client.post("/tareas", json={"descripcion": "T1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "T2", "estado": "en_progreso"})
    response = client.put("/tareas/completar_todas")
    assert response.status_code == 200
    assert response.json()["tareas_actualizadas"] == 2
    get_response = client.get("/tareas")
    assert all(t["estado"] == "completada" for t in get_response.json())

def test_20_completar_todas_sin_tareas():
    response = client.put("/tareas/completar_todas")
    assert response.status_code == 200
    assert response.json()["tareas_actualizadas"] == 0