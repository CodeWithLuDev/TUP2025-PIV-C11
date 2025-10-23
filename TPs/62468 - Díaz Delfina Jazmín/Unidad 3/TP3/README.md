# TP3 - API de Tareas Persistente con SQLite

## 📋 Descripción
Esta es una API REST que permite gestionar una lista de tareas de forma persistente usando una base de datos SQLite. Los datos se mantienen guardados incluso después de reiniciar el servidor.

## 🚀 Cómo iniciar el proyecto

### 1. Instalar las dependencias necesarias
Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pip install fastapi uvicorn pydantic
```

### 2. Iniciar el servidor
Ejecuta el siguiente comando:

```bash
uvicorn main:app --reload
```

El servidor se iniciará en: `http://127.0.0.1:8000`

### 3. Ver la documentación interactiva
Una vez que el servidor esté corriendo, puedes acceder a la documentación automática en:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Estas páginas te permiten probar los endpoints directamente desde el navegador.

## 📚 Endpoints disponibles

### 1. Obtener todas las tareas
**GET** `/tareas`

**Parámetros opcionales:**
- `estado`: Filtra por estado (`pendiente`, `en_progreso`, `completada`)
- `texto`: Busca tareas que contengan este texto
- `prioridad`: Filtra por prioridad (`baja`, `media`, `alta`)
- `orden`: Ordena por fecha (`asc` o `desc`)

**Ejemplos:**
```bash
# Obtener todas las tareas
curl http://127.0.0.1:8000/tareas

# Obtener solo tareas pendientes
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Buscar tareas que contengan "comprar"
curl http://127.0.0.1:8000/tareas?texto=comprar

# Tareas de alta prioridad ordenadas por fecha descendente
curl http://127.0.0.1:8000/tareas?prioridad=alta&orden=desc
```

### 2. Obtener resumen de tareas
**GET** `/tareas/resumen`

Devuelve cuántas tareas hay en cada estado.

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 5,
  "en_progreso": 2,
  "completada": 8
}
```

### 3. Crear una nueva tarea
**POST** `/tareas`

**Cuerpo de la solicitud:**
```json
{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Comprar leche", "estado": "pendiente", "prioridad": "alta"}'
```

### 4. Actualizar una tarea
**PUT** `/tareas/{id}`

**Cuerpo de la solicitud** (todos los campos son opcionales):
```json
{
  "descripcion": "Comprar leche desnatada",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Ejemplo con curl:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### 5. Eliminar una tarea
**DELETE** `/tareas/{id}`

**Ejemplo:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

## 🗂️ Estructura de una tarea

Cada tarea tiene los siguientes campos:

- **id**: Número único que identifica la tarea (se genera automáticamente)
- **descripcion**: Texto que describe la tarea
- **estado**: Estado actual (`pendiente`, `en_progreso`, `completada`)
- **prioridad**: Nivel de importancia (`baja`, `media`, `alta`)
- **fecha_creacion**: Fecha y hora en que se creó la tarea (se genera automáticamente)

## ✅ Verificar la persistencia

Para comprobar que los datos se guardan correctamente:

1. Inicia el servidor y crea algunas tareas
2. Detén el servidor (Ctrl + C en la terminal)
3. Vuelve a iniciar el servidor
4. Consulta las tareas nuevamente - ¡deberían seguir ahí!

## 🧪 Ejecutar los tests

Para ejecutar las pruebas automáticas:

```bash
# Instalar dependencias de testing (si no las tienes)
pip install pytest httpx

# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_00_nombre_del_test -v
```

## 📁 Archivos del proyecto

- `main.py`: Código principal de la API
- `tareas.db`: Base de datos SQLite (se crea automáticamente)
- `README.md`: Este archivo con las instrucciones
- `test_TP3.py`: Archivo con las pruebas automáticas

## ❓ Solución de problemas comunes

### El servidor no inicia
- Verifica que hayas instalado todas las dependencias
- Asegúrate de estar en la carpeta correcta

### Los tests fallan
- Verifica que el servidor esté ejecutándose en el puerto 8000
- Asegúrate de que la base de datos no tenga datos antiguos que interfieran

### No se guardan los datos
- Revisa que el archivo `tareas.db` se esté creando en la misma carpeta
- Verifica los permisos de escritura en la carpeta

## 👨‍💻 Autor
Delfina Jazmin Diaz 

