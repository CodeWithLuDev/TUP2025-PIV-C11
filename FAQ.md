# Preguntas Frecuentes 
1. **¿Qué es una rama y por qué debería usarla?**
- Una rama (branch) es una versión aislada de tu proyecto. Te permite trabajar en una nueva característica o corrección sin afectar el código principal (la rama main). De esta manera, si algo sale mal, el proyecto principal sigue funcionando sin problemas.

    ```bash
    # Paso 1: Crea y cambia a tu nueva rama
    git checkout -b mi-nueva-rama

    # Ahora estás trabajando en 'mi-nueva-rama'
    # ...haz tus cambios en los archivos...

    # Paso 2: Agrega y sube tus cambios a la nueva rama
    git add .
    git commit -m "Añadiendo la nueva característica X"
    git push origin mi-nueva-rama
    ```

2. **¿Qué es un "Pull Request" (PR)?**
- Un Pull Request es una solicitud para fusionar los cambios de tu rama a la rama main del proyecto. Es la forma en que le pides a un revisor (como tu profesor) que mire tu código y lo apruebe antes de que se integre al proyecto principal. **Esta es la manera con la que vamos a trabajar**, no hagan `merge` por si solos.

3. **¿Qué hago si mi rama está desactualizada con main?**
- Esto es muy común y no es un problema. Significa que alguien más ha fusionado sus cambios a la rama main mientras tú estabas trabajando. Para evitar conflictos, debes sincronizar tu rama con la última versión de main antes de que tu PR sea fusionada.

    ```bash
    # 1. Cambia a tu rama de trabajo
    git checkout tu-rama-de-trabajo

    # 2. Sincroniza tu rama con los cambios de 'main'
    #    Esto traerá los cambios y los fusionará en tu rama
    git pull origin main

    # Si hay conflictos, Git te avisará. Debes editarlos manualmente.
    # Abre los archivos con conflictos y elimina las marcas de Git: <<<<<<<, =======, >>>>>>>
    # Una vez resueltos los conflictos, haz un commit para guardar la resolución.

    # 3. Haz un nuevo commit para guardar los cambios (solo si hubo conflictos)
    git add .
    git commit -m "Resolviendo conflictos con la rama main"

    # 4. Sube la rama actualizada a GitHub
    git push origin tu-rama-de-trabajo
    ```

    *Una vez que hagas git push, tu Pull Request se actualizará automáticamente y estará lista para ser revisada.*

4. **¿Qué es un conflicto de fusión ("merge conflict") y cómo lo resuelvo?**
- Un conflicto de fusión ocurre cuando Git no puede fusionar automáticamente dos ramas porque hay cambios contradictorios en la misma línea de código o en el mismo archivo.

- Cómo identificarlo:

- Git te lo indicará en la terminal y marcará las líneas conflictivas en el archivo con <<<<<<<, ======= y >>>>>>>.

- Ejemplo de un conflicto en un archivo:
    ```bash
    <<<<<<< HEAD
        console.log("Código de mi rama");
    =======
        console.log("Código de la rama main");
    >>>>>>> main
    ```
- Cómo resolverlo:

    - Abre el archivo afectado en tu editor de código.

    - Decide qué versión del código quieres mantener o si quieres combinarlas.

    - Elimina todas las marcas de conflicto (<<<<<<<, =======, >>>>>>>).

    - Guarda el archivo.

    - Desde la terminal, agrega el archivo y haz un commit para confirmar que el conflicto está resuelto.

    ```bash
    # Agrega el archivo que resolviste
    git add nombre-del-archivo-con-conflicto.js

    # Haz un commit para guardar la resolución
    git commit -m "Resolviendo el conflicto de fusión"
    ```

5. **¿Qué pasa si múltiples estudiantes suben sus PRs al mismo tiempo?**
- No hay problema. El profesor revisará las PRs una por una. Cuando la primera PR sea aceptada, las demás quedarán desactualizadas.


- **La solución es simple:** El dueño de cada PR desactualizada debe sincronizar su rama con main usando el comando `git pull origin main` y resolver cualquier conflicto que surja. Una vez que su rama esté actualizada, su PR también se actualizará y estará lista para ser revisada.

6. **Si un alumno fusiona su rama con master/main, ¿puede volver a su rama para seguir trabajando, o tiene que crear una nueva?**
- Sí, el alumno puede y debe volver a su rama. No es necesario crear una rama nueva. La fusión (merge) solo integra los cambios de la rama del alumno en la rama principal, pero no elimina la rama original.

7. **Después de fusionar mi rama, ¿esta se actualiza automáticamente con los últimos cambios de la rama master/main?**
- No, los cambios no fluyen en ambas direcciones automáticamente. La rama del alumno permanece como estaba antes del merge. Si quieres actualizar tu rama con los últimos cambios de master/main (como los de tus compañeros), debes hacerlo manualmente.

- Pasos para continuar trabajando en tu rama de forma segura:
    - Cambia a la rama principal:

    ```bash
    git checkout master
    ```

    - Actualiza master con los últimos cambios del proyecto:

    ```bash
    git pull origin master
    ```
    
    - Vuelve a tu rama de trabajo:

    ```bash
    git checkout alumno/Legajo-Nombre
    ```

    - Integra los cambios de master en tu rama:
    
    ```
    git merge master
    ```

8. **¿Cuál es la diferencia entre hacer git merge master (en mi rama) y git merge alumno/Legajo-Nombre (en master)?**
- La diferencia es la dirección en que se fusionan los cambios:

    - git merge master (estando en tu rama): Estás trayendo los cambios de master a tu rama. Esto sirve para mantener tu rama actualizada.

    - git merge alumno/Legajo-Nombre (estando en master): Estás llevando los cambios de tu rama a master. Esto sirve para integrar tu trabajo al proyecto principal.

9. **¿Es necesario mergear mi rama como alumno para que se una a la rama principal del proyecto?**
- Si la idea es que cada alumno use su propia rama para entregar trabajos semanalmente, hacer un merge con la rama principal (main o master) no es lo más óptimo. Si cada alumno hace merge de su rama a la principal, esto podría crear un historial de commits muy desordenado y lleno de conflictos. El merge solo es ideal cuando varias personas han trabajado en una función o corrección de error y necesitan unir sus cambios a la rama principal.

10. **¿Cuál es la manera más optima de entregar mis trabajos semanalmente?**
- La mejor manera de gestionar las entregas semanales es a través de pull requests (PRs). Este es el flujo de trabajo estándar en la industria de la programación y le da el control que necesita el profesor.

- Flujo para el alumno:
    - **Crear y trabajar en su rama**: El alumno ya tiene su rama. En ella, hace todos los commits necesarios para su trabajo práctico.

    - **Subir los cambios**: Una vez que ha terminado el trabajo de la semana, sube su rama al repositorio remoto.

    ```bash
    git push origin nombre-rama-alumno
    ```

    - **Crear un pull request**: Este es el paso clave. Desde la interfaz de GitHub, el alumno crea un pull request que propone unir su rama con la rama principal (main).

        - Le pondrá un nombre claro, como "TP Semana X - Alumno X".

        - En la descripción, puede añadir información relevante sobre lo que hizo.

    - R**evisar el pull request**: El profesor recibirá una notificación de que hay un nuevo pull request. El podrá:

        - Ver todos los cambios de código que el alumno hizo de forma clara.

        - Dejar comentarios directamente en líneas específicas de código para dar feedback.

        - Decidir qué hacer: Una vez que el alumno ha cumplido con los requisitos del trabajo, el profesor tiene dos opciones:
            - **Aceptar y mergear (si es necesario)**: Si el trabajo está perfecto, y el profesor quiere que se una al proyecto principal, el puede hacer clic en "Merge pull request". 

            - **Cerrar el pull request**: Simplemente puede cerrar el PR una vez que ha revisado y calificado el trabajo. Esto indica que la entrega fue completada, sin necesidad de unir el código del alumno a la rama principal.