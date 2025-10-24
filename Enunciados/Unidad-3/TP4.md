# Trabajo Práctico N°4 – Relaciones entre Tablas y Filtros Avanzados

## Objetivos de Aprendizaje

- Diseñar y crear múltiples tablas relacionadas en SQLite.
- Implementar relaciones 1:N (uno a muchos) usando claves foráneas.
- Realizar consultas con JOINs para combinar información de tablas relacionadas.
- Aplicar filtros complejos usando múltiples parámetros de búsqueda.
- Validar la integridad referencial entre tablas.

## Contexto

En el TP3 construiste una API con persistencia usando SQLite, pero todas las tareas existían de forma independiente. En aplicaciones reales, los datos suelen estar relacionados: por ejemplo, las tareas pertenecen a proyectos, los productos a categorías, los comentarios a publicaciones, etc.

En este TP vas a extender tu API para manejar proyectos que contienen tareas, aprendiendo a trabajar con relaciones entre tablas y consultas más sofisticadas.

## Enunciado Práctico

## 1. Diseño de Base de Datos Relacional

Crear/modificar la base de datos tareas.db para incluir las siguientes tablas:

Tabla `Proyectos`

```SQL
id (entero, clave primaria, auto incremental)
nombre (string, no acepta valores nulos, único)
descripcion (string, puede ser nulo)
fecha_creacion (string, no acepta valores nulos)
```

Tabla `tareas` (modificada del TP3)

```SQL
id (entero, clave primaria, auto incremental)
descripcion (string, no acepta valores nulos)
estado (string, no acepta valores nulos)
prioridad (string, no acepta valores nulos)
proyecto_id (entero, clave foránea que referencia a proyectos.id)
fecha_creacion (string, no acepta valores nulos)
```

**Importante**:

- La columna `proyecto_id` debe ser una clave foránea que referencia a `proyectos.id`.
- Configurar `ON DELETE CASCADE` para que al eliminar un proyecto se eliminen automáticamente todas sus tareas asociadas.
- Actualizar la función `init_db()` para crear ambas tablas si no existen.

## 2. CRUD de Proyectos

Implementar los siguientes endpoints para gestionar proyectos:

| Método     | Ruta              | Descripción                            |
| ---------- | ----------------- | -------------------------------------- |
| **GET**    | `/proyectos`      | Lista todos los proyectos.             |
| **GET**    | `/proyectos/{id}` | Obtiene un proyecto específico.        |
| **POST**   | `/proyectos`      | Crea un nuevo proyecto.                |
| **PUT**    | `/proyectos/{id}` | Modifica un proyecto existente.        |
| **DELETE** | `/proyectos/{id}` | Elimina un proyecto y sus tareas.      |

**Requisitos funcionales:**

- Al crear un proyecto, validar que el nombre no esté vacío y no exista otro con el mismo nombre.
- La descripción es opcional.
- Guardar la fecha y hora actual en `fecha_creacion`.
- Al obtener un proyecto (`GET /proyectos/{id}`), incluir un contador de tareas asociadas.

## 3. Tareas Asociadas a Proyectos

Modificar y extender los endpoints de tareas del TP3:

| Método     | Ruta                     | Descripción                                     |
| ---------- | ------------------------ | --------------------------------------          |
| **GET**    | `/proyectos/{id}/tareas` | Lista todas las tareas de un proyecto           |
| **GET**    | `/tareas`                | Lista todas las tareas (de todos los proyectos) |
| **POST**   | `/proyectos/{id}/tareas` | Crea una tarea dentro de un proyecto            |
| **PUT**    | `/tareas/{id}`           | Modifica una tarea (puede cambiar de proyecto)  |
| **DELETE** | `/tareas/{id}`           | Elimina una tarea                               |

**Requisitos funcionales:**

- Al crear una tarea, validar que el `proyecto_id` exista en la tabla proyectos.
- Al listar tareas de un proyecto, devolver 404 si el proyecto no existe.
- Mantener las validaciones del TP3 (descripción no vacía, estados válidos, prioridades válidas).

## 4. Filtros y Búsquedas Avanzadas

Implementar los siguientes filtros usando Query Params:

En `/proyectos`:

- `GET /proyectos?nombre=parcial` → busca proyectos cuyo nombre contenga ese texto.

En `/tareas` y `/proyectos/{id}/tareas`:

- `GET /tareas?estado=pendiente` → filtra por estado.
- `GET /tareas?prioridad=alta` → filtra por prioridad.
- `GET /tareas?proyecto_id=1` → filtra por proyecto (solo en `/tareas`).
- `GET /tareas?estado=completada&prioridad=alta` → múltiples filtros simultáneos.
- `GET /tareas?orden=asc` o `desc` → ordena por fecha de creación.

Los filtros deben poder combinarse (ej: tareas completadas de alta prioridad de un proyecto específico).

## 5. Endpoints de Resumen y Estadísticas

| Método     | Ruta                      | Descripción                                     |
| ---------- | ------------------------- | ----------------------------------------------- |
| **GET**    | `/proyectos/{id}/resumen` | Devuelve estadísticas del proyecto              |
| **GET**    | `/resumen`                | Resumen general de toda la aplicación           |

**Formato de respuesta para** `/proyectos/{id}/resumen`:

```JSON
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Alpha",
  "total_tareas": 15,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 7,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 4,
    "media": 8,
    "alta": 3
  }
}
```

**Formato de respuesta para** `/resumen`:

```JSON
{
  "total_proyectos": 3,
  "total_tareas": 42,
  "tareas_por_estado": {
    "pendiente": 15,
    "en_progreso": 20,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 15
  }
}
```

## 6. Validación con Pydantic Models

Crear modelos Pydantic para validar los datos de entrada:

```python
# Ejemplos de modelos requeridos
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]
```

## 7. Manejo de Errores Específicos

Implementar respuestas de error apropiadas:

- 404: Proyecto o tarea no encontrada.
- 400: Datos inválidos (ej: nombre de proyecto vacío, proyecto_id inexistente).
- 409: Conflicto (ej: nombre de proyecto duplicado).

Incluir mensajes de error descriptivos en español.

## 8. Verificación de Integridad Referencial

Probar los siguientes escenarios:

- Crear un proyecto y agregarle varias tareas.
- Intentar crear una tarea con un proyecto_id que no existe (debe fallar).
- Eliminar un proyecto y verificar que sus tareas también se eliminen.
- Modificar el proyecto_id de una tarea para moverla a otro proyecto.

## Entregable

Subir dentro de la carpeta `TP4`:

- `main.py` – Archivo principal de la API con todos los endpoints.
- `models.py` – Modelos Pydantic para validación.
- `database.py` (opcional) – Funciones de base de datos separadas.
- `tareas.db` – Base de datos con las tablas creadas y algunos datos de prueba.
- `README.md` – Documentación que incluya:
  - Instrucciones para iniciar el servidor.
  - Diagrama o descripción de la estructura de tablas.
  - Ejemplos de requests para cada endpoint (con curl o formato JSON).
  - Explicación de cómo funcionan las relaciones entre tablas.

## Fecha de entrega

**[IMPORTANTE]**

El trabajo debe presentarse hasta el 24 de OCTUBRE de 2025 a las 21:00hs.
