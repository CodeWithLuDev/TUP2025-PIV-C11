# 📱 Manual de Usuario - Sistema de Gestión de Tareas

## 📋 Índice
1. [¿Qué es este sistema?](#qué-es-este-sistema)
2. [Instalación](#instalación)
3. [Cómo iniciar el sistema](#cómo-iniciar-el-sistema)
4. [Guía de uso paso a paso](#guía-de-uso-paso-a-paso)
5. [Ejemplos prácticos](#ejemplos-prácticos)
6. [Preguntas frecuentes](#preguntas-frecuentes)
7. [Solución de problemas](#solución-de-problemas)

---

## 🎯 ¿Qué es este sistema?

Este es un **Sistema de Gestión de Tareas** que te permite:

- ✅ **Crear** tareas con descripción, estado y prioridad
- 📋 **Ver** todas tus tareas organizadas
- ✏️ **Editar** tareas existentes
- 🗑️ **Eliminar** tareas que ya no necesitas
- 🔍 **Buscar** tareas por diferentes criterios
- 📊 **Ver estadísticas** de tus tareas

**Lo mejor:** Todas tus tareas se guardan automáticamente y no se pierden al cerrar el programa.

---

## 💻 Instalación

### Requisitos
- Computadora con Windows, Mac o Linux
- Python 3.7 o superior instalado

### ¿Cómo verifico si tengo Python?

Abre una terminal o símbolo del sistema y escribe:
```bash
python --version
```

Si no tienes Python, descárgalo desde: https://www.python.org/downloads/

### Pasos de Instalación

**Paso 1:** Descarga los archivos del proyecto en una carpeta.

**Paso 2:** Abre una terminal en esa carpeta.

**Paso 3:** Instala las herramientas necesarias:
```bash
pip install fastapi uvicorn pydantic
```

Espera a que se descargue e instale todo (puede tardar 1-2 minutos).

**Paso 4:** ¡Listo! Ya puedes usar el sistema.

---

## 🚀 Cómo Iniciar el Sistema

### Método 1: Desde la Terminal (Recomendado)

1. Abre una terminal en la carpeta del proyecto
2. Escribe este comando:
```bash
uvicorn main:app --reload
```
3. Verás un mensaje como este:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**¡El sistema está funcionando!** 🎉

### Método 2: Usando Visual Studio Code

1. Abre la carpeta del proyecto en VS Code
2. Abre una terminal (Terminal → New Terminal)
3. Escribe: `uvicorn main:app --reload`

### ¿Cómo sé que funciona?

Abre tu navegador web y ve a: http://localhost:8000

Deberías ver información del sistema.

---

## 📖 Guía de Uso Paso a Paso

### 🌐 Interfaz Visual (Recomendado para principiantes)

El sistema tiene una **interfaz visual** que hace todo más fácil.

**Cómo acceder:**
1. Inicia el sistema (ver sección anterior)
2. Abre tu navegador
3. Ve a: http://localhost:8000/docs

¡Verás una pantalla bonita con todos los botones! 🎨

---

### 1️⃣ Crear tu Primera Tarea

**Usando la interfaz visual:**

1. Ve a http://localhost:8000/docs
2. Busca la sección **POST /tareas** (con color verde)
3. Haz click en ella
4. Click en **"Try it out"**
5. Edita el ejemplo:
```json
{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "media"
}
```
6. Click en **"Execute"**
7. ¡Listo! Tu tarea fue creada ✅

**Usando comandos (avanzado):**
```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Comprar leche", "estado": "pendiente", "prioridad": "media"}'
```

---

### 2️⃣ Ver Todas tus Tareas

**Usando la interfaz visual:**

1. Ve a http://localhost:8000/docs
2. Busca **GET /tareas** (con color azul)
3. Click → **"Try it out"** → **"Execute"**
4. Verás la lista de todas tus tareas 📋

**Usando comandos:**
```bash
curl http://localhost:8000/tareas
```

---

### 3️⃣ Buscar Tareas Específicas

Puedes filtrar tus tareas de varias formas:

#### Por Estado
**Ejemplo:** Ver solo tareas pendientes

En la interfaz:
1. Ve a **GET /tareas**
2. Click en **"Try it out"**
3. En el campo **estado** escribe: `pendiente`
4. Click **"Execute"**

#### Por Prioridad
**Ejemplo:** Ver solo tareas de alta prioridad

1. En el campo **prioridad** escribe: `alta`
2. Click **"Execute"**

#### Por Texto
**Ejemplo:** Buscar tareas que contengan "comprar"

1. En el campo **texto** escribe: `comprar`
2. Click **"Execute"**

#### Combinar Filtros
Puedes usar varios filtros a la vez:
- Estado: `pendiente`
- Prioridad: `alta`
- Texto: `urgente`

---

### 4️⃣ Actualizar una Tarea

**Ejemplo:** Marcar una tarea como completada

**Usando la interfaz:**

1. Primero, necesitas el **ID** de la tarea (lo ves al listar tareas)
2. Ve a **PUT /tareas/{id}**
3. Click **"Try it out"**
4. En **id** escribe: `1` (o el número de tu tarea)
5. Edita solo lo que quieres cambiar:
```json
{
  "estado": "completada"
}
```
6. Click **"Execute"**
7. ¡Tarea actualizada! ✨

---

### 5️⃣ Eliminar una Tarea

**Usando la interfaz:**

1. Ve a **DELETE /tareas/{id}** (color rojo)
2. Click **"Try it out"**
3. Escribe el **id** de la tarea: `1`
4. Click **"Execute"**
5. La tarea se eliminó permanentemente 🗑️

⚠️ **Cuidado:** Esta acción no se puede deshacer.

---

### 6️⃣ Ver Estadísticas

**Usando la interfaz:**

1. Ve a **GET /tareas/resumen**
2. Click **"Try it out"** → **"Execute"**
3. Verás algo como:
```json
{
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 2,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 2,
    "media": 5,
    "alta": 3
  }
}
```

Esto te muestra:
- Cuántas tareas tienes en total
- Cuántas están pendientes, en progreso o completadas
- Cuántas son de baja, media o alta prioridad

---

### 7️⃣ Completar Todas las Tareas

¿Terminaste todo? Puedes marcar todas como completadas de una vez:

**Usando la interfaz:**

1. Ve a **PUT /tareas/completar_todas**
2. Click **"Try it out"** → **"Execute"**
3. ¡Todas tus tareas ahora están completadas! 🎉

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Lista de Compras

**Crear las tareas:**
```json
{"descripcion": "Comprar pan", "estado": "pendiente", "prioridad": "alta"}
{"descripcion": "Comprar leche", "estado": "pendiente", "prioridad": "alta"}
{"descripcion": "Comprar frutas", "estado": "pendiente", "prioridad": "media"}
```

**Filtrar solo compras importantes:**
- Estado: `pendiente`
- Prioridad: `alta`

**Marcar como comprado:**
- Actualiza el estado a `completada`

---

### Ejemplo 2: Tareas de Estudio
```json
{"descripcion": "Estudiar FastAPI", "estado": "en_progreso", "prioridad": "alta"}
{"descripcion": "Hacer ejercicios", "estado": "pendiente", "prioridad": "media"}
{"descripcion": "Leer documentación", "estado": "pendiente", "prioridad": "baja"}
```

**Ver tu progreso:**
- Usa el endpoint `/tareas/resumen`

---

### Ejemplo 3: Organizar el Día

**Por la mañana:**
```json
{"descripcion": "Hacer ejercicio", "estado": "pendiente", "prioridad": "alta"}
{"descripcion": "Revisar emails", "estado": "pendiente", "prioridad": "media"}
```

**Después de hacer ejercicio:**
- Actualiza "Hacer ejercicio" a estado `completada`

**Al final del día:**
- Usa `/tareas/resumen` para ver qué completaste

---

## ❓ Preguntas Frecuentes

### ¿Mis tareas se guardan automáticamente?
**Sí.** Todas las tareas se guardan en una base de datos llamada `tareas.db`. Puedes cerrar el programa y tus tareas seguirán ahí cuando lo vuelvas a abrir.

### ¿Puedo usar el sistema sin internet?
**Sí.** El sistema funciona completamente en tu computadora. Solo necesitas internet para instalarlo la primera vez.

### ¿Qué significa cada estado?
- **pendiente**: La tarea aún no empezó
- **en_progreso**: Estás trabajando en ella
- **completada**: Ya la terminaste ✅

### ¿Qué significa cada prioridad?
- **baja**: No es urgente
- **media**: Importante pero no urgente
- **alta**: ¡Hazla pronto! 🔥

### ¿Puedo cambiar solo el estado sin cambiar la descripción?
**Sí.** Al actualizar, solo incluye lo que quieres cambiar. El resto queda igual.

### ¿Puedo deshacer una eliminación?
**No.** Las tareas eliminadas se borran permanentemente. Ten cuidado al eliminar.

### ¿Puedo acceder desde mi celular?
**Sí**, si tu celular está en la misma red WiFi. Usa la IP de tu computadora en lugar de `localhost`.

---

## 🔧 Solución de Problemas

### Problema: "No se puede conectar a localhost:8000"

**Solución:**
1. Verifica que el sistema esté corriendo (debe estar en la terminal)
2. Si no está corriendo, ejecuta: `uvicorn main:app --reload`
3. Espera a ver el mensaje "Application startup complete"

---

### Problema: "pip no se reconoce como comando"

**Solución:**
- **Windows**: Reinstala Python y marca "Add Python to PATH" durante la instalación
- **Mac/Linux**: Usa `pip3` en lugar de `pip`

---

### Problema: "El puerto 8000 ya está en uso"

**Solución:**

**Opción 1:** Cierra el programa que está usando el puerto 8000

**Opción 2:** Usa otro puerto:
```bash
uvicorn main:app --reload --port 8001
```
Luego accede a: http://localhost:8001

---

### Problema: "Error al crear tarea"

**Causas comunes:**
- ✅ Verifica que la descripción no esté vacía
- ✅ El estado debe ser: `pendiente`, `en_progreso` o `completada`
- ✅ La prioridad debe ser: `baja`, `media` o `alta`

---

### Problema: "No encuentro una tarea que creé"

**Solución:**
1. Lista todas las tareas: **GET /tareas**
2. Verifica el ID de la tarea
3. Busca por texto si no recuerdas el ID

---

### Problema: "Reinicié la computadora y mis tareas desaparecieron"

**Esto NO debería pasar.** Las tareas están en `tareas.db`.

**Verifica:**
1. ¿Estás en la misma carpeta donde trabajabas?
2. ¿Existe el archivo `tareas.db` en la carpeta?
3. Si no existe, el sistema crea una base de datos nueva (vacía)

---

## 📞 Información Técnica

### Archivos del Sistema
```
TP3/
├── main.py           → Código principal del sistema
├── tareas.db         → Base de datos (tus tareas están aquí)
├── README.md         → Este manual
└── test_TP3.py       → Pruebas del sistema
```

### Estados Válidos
- `pendiente` - Tarea no iniciada
- `en_progreso` - Tarea en progreso
- `completada` - Tarea terminada

### Prioridades Válidas
- `baja` - Prioridad baja
- `media` - Prioridad media (valor por defecto)
- `alta` - Prioridad alta

### Tecnologías Usadas
- **FastAPI**: Framework web moderno
- **SQLite**: Base de datos ligera
- **Python**: Lenguaje de programación
- **Uvicorn**: Servidor web

---

## 🎓 Consejos de Uso

### ✨ Buenas Prácticas

1. **Sé específico en las descripciones**
   - ❌ Malo: "Hacer cosas"
   - ✅ Bueno: "Terminar informe de ventas del mes"

2. **Usa prioridades inteligentemente**
   - No hagas todo "alta prioridad"
   - Reserva "alta" para lo verdaderamente urgente

3. **Actualiza el estado regularmente**
   - Cambia a "en_progreso" cuando empiezas
   - Cambia a "completada" cuando terminas

4. **Usa filtros para organizarte**
   - Por la mañana: Filtra por `prioridad=alta`
   - Por la tarde: Filtra por `estado=pendiente`

5. **Revisa tu resumen diariamente**
   - Te ayuda a ver tu progreso
   - Te motiva a completar más tareas

---

## 📊 Atajos Útiles

### URLs Rápidas

- **Interfaz visual**: http://localhost:8000/docs
- **Ver todas las tareas**: http://localhost:8000/tareas
- **Ver resumen**: http://localhost:8000/tareas/resumen
- **Filtrar pendientes**: http://localhost:8000/tareas?estado=pendiente
- **Filtrar alta prioridad**: http://localhost:8000/tareas?prioridad=alta

---

## 🎯 Cómo Detener el Sistema

Cuando termines de usar el sistema:

1. Ve a la terminal donde está corriendo
2. Presiona `Ctrl + C` (Windows/Linux) o `Cmd + C` (Mac)
3. Verás un mensaje de "Shutting down"
4. ¡Listo! El sistema se detuvo

**No te preocupes:** Tus tareas están guardadas en `tareas.db`.

---

## 📝 Notas Importantes

- ⚠️ **No elimines** el archivo `tareas.db` - ahí están tus tareas
- 💾 El sistema guarda automáticamente - no necesitas un botón "Guardar"
- 🔒 Tus datos están solo en tu computadora - nadie más puede verlos
- 🚀 Puedes crear tantas tareas como quieras - no hay límite

---

## 👨‍💻 Información del Proyecto

**Nombre**: Sistema de Gestión de Tareas  
**Versión**: 3.0  
**Autor**: [Tu Nombre]  
**Fecha**: Octubre 2025  
**Materia**: Programación de Aplicaciones  
**Trabajo**: Práctico N°3  

---

## 📬 Contacto y Soporte

Si tienes problemas o preguntas:
1. Revisa la sección "Preguntas Frecuentes"
2. Revisa "Solución de Problemas"
3. Contacta a tu profesor o asistente

---

## 🎉 ¡Comienza a Usar el Sistema!

**Pasos rápidos para empezar:**

1. ✅ Abre una terminal en la carpeta del proyecto
2. ✅ Ejecuta: `uvicorn main:app --reload`
3. ✅ Abre tu navegador en: http://localhost:8000/docs
4. ✅ Crea tu primera tarea
5. ✅ ¡Empieza a organizarte! 🚀

---

**¡Gracias por usar el Sistema de Gestión de Tareas!** 💙

Si este manual te resultó útil, ¡compártelo con tus compañeros! 📚