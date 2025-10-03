"""
Test de autocorrección para TP3.1 - Introducción a FastAPI
Ejecutar con: python -m pytest test_TP1.py -v
O simplemente: python test_TP1.py
"""

import pytest
import requests
import json
import time
import subprocess
import sys
from typing import Dict, Any, List

class TestAgendaAPI:
    """
    Clase de test para verificar la implementación de la Agenda API
    """
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @classmethod
    def setup_class(cls):
        """Configuración inicial antes de ejecutar los tests"""
        print("\n" + "="*60)
        print("🚀 INICIANDO TESTS DE AUTOCORRECCIÓN")
        print("TP3.1: Introducción a FastAPI - Servidor Básico")
        print("="*60)
        
        # Verificar que el servidor esté corriendo
        try:
            response = requests.get(f"{cls.BASE_URL}/", timeout=5)
            print("✅ Servidor detectado y funcionando")
        except requests.exceptions.RequestException:
            print("❌ ERROR: El servidor no está corriendo")
            print("💡 Ejecuta primero: uvicorn main:app --reload")
            sys.exit(1)

    def test_01_endpoint_raiz_existe(self):
        """Test 1: Verificar que existe el endpoint raíz"""
        print("\n📋 Test 1: Verificando endpoint raíz...")
        
        response = requests.get(f"{self.BASE_URL}/")
        
        assert response.status_code == 200, "El endpoint raíz debe retornar status 200"
        print("✅ Endpoint raíz responde correctamente")

    def test_02_mensaje_bienvenida_formato(self):
        """Test 2: Verificar formato del mensaje de bienvenida"""
        print("\n📋 Test 2: Verificando formato del mensaje de bienvenida...")
        
        response = requests.get(f"{self.BASE_URL}/")
        data = response.json()
        
        assert "mensaje" in data, "La respuesta debe contener la clave 'mensaje'"
        assert "Bienvenido" in data["mensaje"], "El mensaje debe contener 'Bienvenido'"
        assert "Agenda de Contactos" in data["mensaje"], "El mensaje debe mencionar 'Agenda de Contactos'"
        
        print("✅ Mensaje de bienvenida tiene el formato correcto")
        print(f"   Mensaje: {data['mensaje']}")

    def test_03_endpoint_contactos_existe(self):
        """Test 3: Verificar que existe el endpoint /contactos"""
        print("\n📋 Test 3: Verificando endpoint /contactos...")
        
        response = requests.get(f"{self.BASE_URL}/contactos")
        
        assert response.status_code == 200, "El endpoint /contactos debe retornar status 200"
        print("✅ Endpoint /contactos responde correctamente")

    def test_04_contactos_es_lista_json(self):
        """Test 4: Verificar que /contactos devuelve una lista JSON"""
        print("\n📋 Test 4: Verificando formato JSON de contactos...")
        
        response = requests.get(f"{self.BASE_URL}/contactos")
        data = response.json()
        
        assert isinstance(data, list), "Los contactos deben ser una lista"
        assert len(data) >= 2, "Debe haber al menos 2 contactos"
        
        print(f"✅ Contactos en formato lista JSON ({len(data)} contactos)")

    def test_05_estructura_contactos(self):
        """Test 5: Verificar estructura de los contactos"""
        print("\n📋 Test 5: Verificando estructura de contactos...")
        
        response = requests.get(f"{self.BASE_URL}/contactos")
        contactos = response.json()
        
        campos_requeridos = ["nombre", "apellido", "edad", "teléfono", "email"]
        
        for i, contacto in enumerate(contactos):
            for campo in campos_requeridos:
                assert campo in contacto, f"Contacto {i} debe tener el campo '{campo}'"
            
            # Verificar tipos de datos
            assert isinstance(contacto["nombre"], str), "nombre debe ser string"
            assert isinstance(contacto["apellido"], str), "apellido debe ser string"
            assert isinstance(contacto["edad"], int), "edad debe ser entero"
            assert isinstance(contacto["teléfono"], str), "teléfono debe ser string"
            assert isinstance(contacto["email"], str), "email debe ser string"
        
        print("✅ Todos los contactos tienen la estructura correcta")
        print(f"   Campos verificados: {', '.join(campos_requeridos)}")

    def test_06_contactos_ejemplo_especificos(self):
        """Test 6: Verificar contactos específicos del ejemplo"""
        print("\n📋 Test 6: Verificando contactos específicos del ejemplo...")
        
        response = requests.get(f"{self.BASE_URL}/contactos")
        contactos = response.json()
        
        # Buscar Juan Pérez
        juan_encontrado = any(
            c["nombre"] == "Juan" and c["apellido"] == "Pérez" and c["edad"] == 30
            for c in contactos
        )
        
        # Buscar José Gómez  
        jose_encontrado = any(
            c["nombre"] == "José" and c["apellido"] == "Gómez" and c["edad"] == 25
            for c in contactos
        )
        
        assert juan_encontrado, "Debe existir el contacto Juan Pérez, 30 años"
        assert jose_encontrado, "Debe existir el contacto José Gómez, 25 años"
        
        print("✅ Contactos del ejemplo encontrados:")
        print("   - Juan Pérez (30 años)")
        print("   - José Gómez (25 años)")

    def test_07_manejo_errores_404(self):
        """Test 7: Verificar manejo de errores 404"""
        print("\n📋 Test 7: Verificando manejo de errores 404...")
        
        # Intentar acceder a una ruta inexistente
        response = requests.get(f"{self.BASE_URL}/ruta-inexistente")
        
        assert response.status_code == 404, "Rutas inexistentes deben retornar 404"
        
        print("✅ Manejo de errores 404 funciona correctamente")

    def test_08_headers_content_type(self):
        """Test 8: Verificar headers de respuesta"""
        print("\n📋 Test 8: Verificando headers de respuesta...")
        
        response = requests.get(f"{self.BASE_URL}/")
        
        assert "application/json" in response.headers.get("content-type", ""), \
            "Las respuestas deben ser application/json"
        
        print("✅ Headers de respuesta correctos (application/json)")

    def test_09_rendimiento_basico(self):
        """Test 9: Test básico de rendimiento"""
        print("\n📋 Test 9: Verificando rendimiento básico...")
        
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/contactos")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response_time < 2.0, "La respuesta debe ser menor a 2 segundos"
        
        print(f"✅ Rendimiento aceptable ({response_time:.3f}s)")

    def test_10_documentacion_automatica(self):
        """Test 10: Verificar que la documentación automática esté disponible"""
        print("\n📋 Test 10: Verificando documentación automática...")
        
        response = requests.get(f"{self.BASE_URL}/docs")
        
        assert response.status_code == 200, "La documentación debe estar disponible en /docs"
        
        print("✅ Documentación automática disponible en /docs")


def mostrar_resumen_final():
    """Mostrar resumen final de los tests"""
    print("\n" + "="*60)
    print("📊 RESUMEN DE AUTOCORRECCIÓN")
    print("="*60)
    print("✅ Si todos los tests pasaron: ¡Excelente trabajo!")
    print("❌ Si algún test falló: Revisa la implementación")
    print("\n💡 Recordatorios:")
    print("   - Ejecuta el servidor con: uvicorn main:app --reload")
    print("   - Visita la documentación en: http://127.0.0.1:8000/docs")
    print("   - Los contactos deben estar hardcoded en memoria")
    print("="*60)


if __name__ == "__main__":
    # Ejecutar tests si se corre el archivo directamente
    import os
    
    # Verificar que pytest esté instalado
    try:
        import pytest
        print("🔧 Ejecutando tests con pytest...")
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("⚠️  pytest no está instalado. Ejecutando tests básicos...")
        
        # Ejecutar tests manualmente
        test_instance = TestAgendaAPI()
        test_instance.setup_class()
        
        tests = [
            test_instance.test_01_endpoint_raiz_existe,
            test_instance.test_02_mensaje_bienvenida_formato,
            test_instance.test_03_endpoint_contactos_existe,
            test_instance.test_04_contactos_es_lista_json,
            test_instance.test_05_estructura_contactos,
            test_instance.test_06_contactos_ejemplo_especificos,
            test_instance.test_07_manejo_errores_404,
            test_instance.test_08_headers_content_type,
            test_instance.test_09_rendimiento_basico,
            test_instance.test_10_documentacion_automatica,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
            except Exception as e:
                print(f"❌ {test.__name__}: {e}")
                failed += 1
        
        print(f"\n📊 Resultados: {passed} pasaron, {failed} fallaron")
    
    mostrar_resumen_final()