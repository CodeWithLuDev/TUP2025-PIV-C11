import pytest
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

# Fixture para limpiar la base de datos antes de cada test
@pytest.fixture(autouse=True)
def limpiar_db():
    main.tareas_db.clear()
    main.contador_id = 1
    yield
    main.tareas_db.clear()

# ==================== TESTS GET /tareas ====================

def test_01_obtener_tareas_vacia():
    """Test: Obtener lista vacía cuando no hay tareas"""
    response = client.get("/tareas")
    assert response.status_code == 200
    assert response.json() == []

def test_02_obtener_todas_las_tareas():
    """Test: Obtener todas las tareas creadas"""
    # Crear tareas
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "completada"})
    
    response = client.get("/tareas")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_03_filtrar_tareas_por_estado_pendiente():
    """Test: Filtrar tareas por estado 'pendiente'"""
    client.post("/tareas", json={"descripcion": "Tarea pendiente", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea completada", "estado": "completada"})
    
    response = client.get("/tareas?estado=pendiente")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["estado"] == "pendiente"

def test_04_filtrar_tareas_por_estado_en_progreso():
    """Test: Filtrar tareas por estado 'en_progreso'"""
    client.post("/tareas", json={"descripcion": "Tarea en progreso", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "Tarea pendiente", "estado": "pendiente"})
    
    response = client.get("/tareas?estado=en_progreso")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["estado"] == "en_progreso"

def test_05_buscar_tareas_por_texto():
    """Test: Buscar tareas que contengan texto específico"""
    client.post("/tareas", json={"descripcion": "Comprar leche", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Estudiar matemáticas", "estado": "pendiente"})
    
    response = client.get("/tareas?texto=leche")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "leche" in response.json()[0]["descripcion"].lower()

def test_06_buscar_tareas_texto_no_encontrado():
    """Test: Buscar tareas con texto que no existe"""
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    
    response = client.get("/tareas?texto=inexistente")
    assert response.status_code == 200
    assert len(response.json()) == 0

# ==================== TESTS POST /tareas ====================

def test_07_crear_tarea_exitosamente():
    """Test: Crear una tarea correctamente"""
    response = client.post("/tareas", json={
        "descripcion": "Nueva tarea",
        "estado": "pendiente"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1  # Verificar que tenga un ID válido
    assert data["descripcion"] == "Nueva tarea"
    assert data["estado"] == "pendiente"
    assert "fecha_creacion" in data

def test_08_crear_tarea_con_descripcion_vacia():
    """Test: Intentar crear tarea con descripción vacía (debe fallar)"""
    response = client.post("/tareas", json={
        "descripcion": "",
        "estado": "pendiente"
    })
    assert response.status_code == 422  # Unprocessable Entity

def test_09_crear_tarea_con_espacios_en_blanco():
    """Test: Intentar crear tarea solo con espacios (debe fallar)"""
    response = client.post("/tareas", json={
        "descripcion": "   ",
        "estado": "pendiente"
    })
    assert response.status_code == 422

def test_10_crear_tarea_con_estado_invalido():
    """Test: Intentar crear tarea con estado no válido (debe fallar)"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea test",
        "estado": "estado_invalido"
    })
    assert response.status_code == 422

def test_11_crear_tarea_sin_estado():
    """Test: Crear tarea sin especificar estado (debe usar 'pendiente' por defecto)"""
    response = client.post("/tareas", json={
        "descripcion": "Tarea sin estado"
    })
    assert response.status_code == 201
    assert response.json()["estado"] == "pendiente"

# ==================== TESTS PUT /tareas/{id} ====================

def test_12_actualizar_tarea_existente():
    """Test: Actualizar una tarea existente correctamente"""
    # Crear tarea
    crear = client.post("/tareas", json={"descripcion": "Tarea original", "estado": "pendiente"})
    tarea_id = crear.json()["id"]
    
    # Actualizar
    response = client.put(f"/tareas/{tarea_id}", json={
        "descripcion": "Tarea actualizada",
        "estado": "completada"
    })
    assert response.status_code == 200
    assert response.json()["descripcion"] == "Tarea actualizada"
    assert response.json()["estado"] == "completada"

def test_13_actualizar_tarea_inexistente():
    """Test: Intentar actualizar tarea que no existe (debe devolver 404)"""
    response = client.put("/tareas/999", json={
        "descripcion": "Nueva descripción",
        "estado": "pendiente"
    })
    assert response.status_code == 404
    data = response.json()
    # FastAPI envuelve el error en "detail"
    assert "detail" in data
    assert "error" in str(data["detail"])

def test_14_actualizar_solo_estado():
    """Test: Actualizar solo el estado de una tarea"""
    crear = client.post("/tareas", json={"descripcion": "Tarea test", "estado": "pendiente"})
    tarea_id = crear.json()["id"]
    
    response = client.put(f"/tareas/{tarea_id}", json={"estado": "en_progreso"})
    assert response.status_code == 200
    assert response.json()["estado"] == "en_progreso"
    assert response.json()["descripcion"] == "Tarea test"

# ==================== TESTS DELETE /tareas/{id} ====================

def test_15_eliminar_tarea_existente():
    """Test: Eliminar una tarea existente correctamente"""
    crear = client.post("/tareas", json={"descripcion": "Tarea a eliminar", "estado": "pendiente"})
    tarea_id = crear.json()["id"]
    
    response = client.delete(f"/tareas/{tarea_id}")
    assert response.status_code == 200
    assert "mensaje" in response.json()
    
    # Verificar que ya no existe
    response_get = client.get("/tareas")
    assert len(response_get.json()) == 0

def test_16_eliminar_tarea_inexistente():
    """Test: Intentar eliminar tarea que no existe (debe devolver 404)"""
    response = client.delete("/tareas/999")
    assert response.status_code == 404
    data = response.json()
    # FastAPI envuelve el error en "detail"
    assert "detail" in data
    assert "error" in str(data["detail"])

# ==================== TESTS GET /tareas/resumen ====================

def test_17_resumen_tareas():
    """Test: Obtener resumen con contador de tareas por estado"""
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "Tarea 4", "estado": "completada"})
    
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["pendiente"] == 2
    assert data["en_progreso"] == 1
    assert data["completada"] == 1

def test_18_resumen_sin_tareas():
    """Test: Obtener resumen cuando no hay tareas"""
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["pendiente"] == 0
    assert data["en_progreso"] == 0
    assert data["completada"] == 0

# ==================== TESTS PUT /tareas/completar_todas ====================

def test_19_completar_todas_las_tareas():
    """Test: Marcar todas las tareas como completadas"""
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "pendiente"})
    
    response = client.put("/tareas/completar_todas")
    assert response.status_code == 200
    assert "mensaje" in response.json()
    
    # Verificar que todas estén completadas
    response_tareas = client.get("/tareas")
    tareas = response_tareas.json()
    for tarea in tareas:
        assert tarea["estado"] == "completada"

def test_20_completar_todas_sin_tareas():
    """Test: Intentar completar todas cuando no hay tareas"""
    response = client.put("/tareas/completar_todas")
    assert response.status_code == 200
    assert "No hay tareas" in response.json()["mensaje"]