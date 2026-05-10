# Soluciones Semana 5 - DevOps en la practica

## Resumen

La parte tecnica del enunciado queda preparada en el proyecto con integracion continua basica para el backend Django.

Se ha realizado y verificado:

- ejecucion local de los tests del backend
- creacion del workflow de GitHub Actions
- definicion de los pasos exactos del pipeline
- comprobacion local del comando que debe ejecutar CI

Archivo principal creado:

- `.github/workflows/ci.yml`

## Ejercicio 1

### Comprobacion local del backend

Se ha ejecutado este comando en la raiz del proyecto:

```bash
python manage.py test
```

Resultado obtenido:

```text
Found 151 test(s).
System check identified no issues (0 silenced).
.......................................................................................................................................................
----------------------------------------------------------------------
Ran 151 tests in 44.424s

OK
```

### Nota breve

Todos los tests pasan en local en la rama actual.

Si fue necesario corregir varios elementos antes de continuar con la configuracion del CI:

- metodos auxiliares del modelo `LibraryEntry`
- modulo `library/validators.py`
- endpoint `GET /api/health/`
- endpoint `POST /api/auth/logout/`
- endpoint `POST /api/users/me/password/`
- soporte de `PUT` en `/api/library/entries/<id>/`

### Sobre la actualizacion del repositorio

Se ha consultado el estado remoto con `git fetch origin`.

Situacion detectada:

- la rama local activa es `Optativa-Semana3`
- existe una rama remota `origin/Servidor-Semana4`
- la rama local activa no es la misma que la rama remota usada en semanas anteriores

Por tanto, antes de hacer una entrega final en GitHub conviene decidir en que rama se quiere publicar la solucion de la semana 5 para no mezclar historiales.

## Ejercicio 2

### Workflow creado

Se ha creado el archivo:

```text
.github/workflows/ci.yml
```

Contenido funcional del workflow:

- se ejecuta en cada `push`
- hace `checkout` del repositorio
- instala Python `3.12`
- instala dependencias desde `requirements.txt`
- ejecuta `python manage.py test`

### Enlace directo esperado en GitHub

Cuando el archivo este subido al repositorio, el enlace directo sera:

```text
https://github.com/adriangarciaam/Ejercicios-evaluables-UA6/blob/<rama>/.github/workflows/ci.yml
```

Sustituye `<rama>` por la rama donde publiques la solucion.

## Ejercicio 3

### Que ocurrira al subir un cambio

Con el workflow ya creado, al hacer un `push` GitHub Actions ejecutara automaticamente estos pasos:

1. `Checkout repository`
2. `Set up Python`
3. `Install dependencies`
4. `Run backend tests`

### Orden y resultado esperado

El orden es secuencial:

1. clonado del codigo
2. preparacion del entorno Python
3. instalacion de dependencias
4. ejecucion de tests

Si el repositorio contiene el mismo codigo que se ha probado en local, el resultado esperado es una ejecucion correcta en verde.

### Cambio pequeno recomendado para disparar el workflow

Puedes usar este mismo archivo de soluciones como cambio pequeno de prueba, o anadir una linea de comentario a cualquier archivo no sensible.

## Ejercicio 4

### Como provocar un fallo controlado

La forma mas segura es modificar temporalmente un valor esperado en un test, hacer `push`, observar el fallo y despues restaurar el valor correcto.

Ejemplo de procedimiento:

1. cambiar temporalmente una asercion en un test
2. subir el cambio
3. revisar en GitHub Actions el paso `Run backend tests`
4. localizar el nombre del test fallido y el mensaje de error
5. restaurar el valor correcto
6. volver a subir los cambios

### Que error deberias ver

El workflow fallaria en el ultimo paso:

```text
Run backend tests
```

GitHub Actions mostraria:

- el nombre del test que falla
- la diferencia entre valor esperado y valor real
- el estado final del job como `failed`

### Como se soluciona

Se revierte el cambio temporal introducido en el test y se vuelve a subir el codigo. En la siguiente ejecucion, el pipeline deberia volver a quedar en verde.

## Entrega

Con lo que ya queda preparado en local, para completar la entrega en GitHub solo faltaria:

1. publicar `.github/workflows/ci.yml` en la rama elegida
2. hacer un `push` para lanzar el workflow
3. capturar una ejecucion correcta
4. provocar un fallo temporal y capturar la ejecucion fallida
5. corregirlo y capturar la ejecucion final correcta
