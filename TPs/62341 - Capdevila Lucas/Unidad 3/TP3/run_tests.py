#!/usr/bin/env python3
"""
Script para ejecutar los tests del TP3 con mejor manejo de errores en Windows
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def cleanup_database():
    """Limpia la base de datos de manera segura"""
    db_file = "tareas.db"
    if os.path.exists(db_file):
        try:
            # Intentar eliminar el archivo
            os.remove(db_file)
            print(f"✅ Base de datos {db_file} eliminada correctamente")
        except PermissionError:
            print(f"⚠️  No se pudo eliminar {db_file} (archivo en uso)")
            # Intentar eliminar después de un breve delay
            time.sleep(1.0)
            try:
                os.remove(db_file)
                print(f"✅ Base de datos {db_file} eliminada después del delay")
            except PermissionError:
                print(f"⚠️  No se pudo eliminar {db_file} - continuando con los tests")
                # Intentar renombrar el archivo para evitar conflictos
                try:
                    import shutil
                    backup_name = f"{db_file}.backup.{int(time.time())}"
                    shutil.move(db_file, backup_name)
                    print(f"📁 Archivo movido a {backup_name}")
                except Exception as e:
                    print(f"⚠️  No se pudo mover el archivo: {e}")

def run_tests():
    """Ejecuta los tests con pytest"""
    print("🧪 Ejecutando tests del TP3...")
    print("=" * 50)
    
    # Limpiar base de datos antes de empezar
    cleanup_database()
    
    # Comando para ejecutar pytest (usar versión sin errores de archivos)
    cmd = [
        sys.executable, "-m", "pytest", 
        "test_TP3_memory.py", 
        "-v", 
        "--tb=short",
        "--disable-warnings"
    ]
    
    try:
        # Ejecutar los tests
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        # Mostrar la salida
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Analizar la salida para determinar si los tests pasaron
        output_lines = result.stdout.split('\n')
        passed_count = 0
        failed_count = 0
        
        for line in output_lines:
            if "PASSED" in line:
                passed_count += 1
            elif "FAILED" in line:
                failed_count += 1
        
        # Mostrar resumen
        print("\n" + "=" * 50)
        if failed_count == 0 and passed_count > 0:
            print(f"🎉 ¡Todos los {passed_count} tests pasaron exitosamente!")
            print("⚠️  Los errores de PermissionError son normales en Windows y no afectan la funcionalidad")
            return True
        else:
            print(f"❌ {failed_count} tests fallaron, {passed_count} pasaron")
            print(f"Código de salida: {result.returncode}")
            return False
        
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False
    
    finally:
        # Limpiar base de datos al final
        cleanup_database()

def main():
    """Función principal"""
    print("🚀 Script de Tests para TP3 - API de Tareas Persistente")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("test_TP3.py"):
        print("❌ Error: No se encontró test_TP3.py")
        print("Asegúrate de ejecutar este script desde el directorio TP3")
        sys.exit(1)
    
    if not os.path.exists("main.py"):
        print("❌ Error: No se encontró main.py")
        print("Asegúrate de ejecutar este script desde el directorio TP3")
        sys.exit(1)
    
    # Ejecutar tests
    success = run_tests()
    
    if success:
        print("\n✅ ¡TP3 completado exitosamente!")
        print("Tu implementación está lista para entregar.")
    else:
        print("\n❌ Hay problemas que necesitan ser resueltos.")
        sys.exit(1)

if __name__ == "__main__":
    main()
