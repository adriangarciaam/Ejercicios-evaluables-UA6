# Soluciones Semana 7 - Dev Containers

Fecha de comprobacion: 7 de mayo de 2026.

## Ejercicio 1

### 1. Comprobacion de Docker

Docker esta instalado y funcionando correctamente en el equipo.

Comandos usados:

```powershell
docker version
docker-compose version
docker ps
```

Resultado resumido:

- Docker Desktop responde correctamente.
- El daemon de Docker esta activo.
- Docker Compose esta disponible.

### 2. Comprobacion del proyecto con Docker Compose

Se ha preparado el proyecto para ejecutarse con Docker Compose creando estos archivos:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

Comando usado:

```powershell
docker-compose up --build -d
```

Verificaciones realizadas:

```powershell
docker-compose ps
docker-compose logs --tail=40 backend
Invoke-WebRequest http://127.0.0.1:8000/api/health/ -UseBasicParsing
```

Resultado:

- El contenedor del backend se crea correctamente.
- Django arranca dentro del contenedor.
- La URL `http://127.0.0.1:8000/api/health/` responde con `{"status": "ok"}`.

### 3. Extensiones necesarias en el IDE

Extensiones comprobadas en VS Code:

- `ms-vscode-remote.remote-containers`
- `ms-azuretools.vscode-docker`

Comprobacion realizada mediante el listado de extensiones instalado en el equipo.

### 4. Archivos de configuracion de contenedores localizados

Archivos relevantes del proyecto:

- `.devcontainer/devcontainer.json`
- `docker-compose.yml`
- `Dockerfile`
- `.dockerignore`

## Ejercicio 2

Se ha creado la carpeta `.devcontainer` en la raiz del proyecto y dentro de ella el archivo `devcontainer.json`.

Configuracion aplicada:

- usa el archivo `docker-compose.yml` del proyecto
- se conecta al servicio `backend`
- abre el proyecto dentro de `/workspace`
- reenvia automaticamente el puerto `8000`

Archivo creado:

- `.devcontainer/devcontainer.json`

Comprobacion tecnica realizada:

- el servicio `backend` levanta correctamente con Docker Compose
- el proyecto responde por HTTP en `http://127.0.0.1:8000/`

Nota:

La accion `Reopen in Container` debe ejecutarse manualmente desde VS Code, pero la configuracion necesaria para hacerlo ya queda preparada en el repositorio.

## Ejercicio 3

Se ha modificado `devcontainer.json` para instalar automaticamente estas extensiones dentro del contenedor:

- `ms-python.vscode-pylance`
- `redhat.java`

### Respuestas breves

`ms-python.vscode-pylance`:
mejora el autocompletado, el analisis estatico, la navegacion por el codigo y la deteccion temprana de errores en proyectos Python como este backend Django.

`redhat.java`:
aporta soporte para proyectos Java y permite que cualquier desarrollador que trabaje tambien con herramientas o servicios Java tenga el entorno listo desde el primer momento.

Instalar extensiones automaticamente en el Dev Container es util porque:

- evita configuraciones manuales distintas entre miembros del equipo
- reduce errores de entorno
- acelera la puesta en marcha del proyecto
- garantiza una experiencia de desarrollo mas consistente

## Ejercicio 4

Para simular la comprobacion con otro desarrollador, se ha creado una copia local del proyecto en:

- `output/devcontainer-check`

Sobre esa copia se ha realizado una verificacion independiente.

Comandos usados:

```powershell
docker-compose up --build -d
docker-compose ps
docker-compose logs --tail=40 backend
Invoke-WebRequest http://127.0.0.1:8000/api/health/ -UseBasicParsing
```

Resultado:

- el contenedor se crea correctamente
- el servidor de desarrollo arranca correctamente
- el proyecto es accesible desde el navegador mediante `http://127.0.0.1:8000/`

### Problema adicional detectado

Al ejecutar una validacion mas profunda con:

```powershell
docker-compose exec -T backend python manage.py test
```

aparece este error:

- `ModuleNotFoundError: No module named 'library.catalog_service'`

Herramientas o comandos utiles para investigarlo:

- `docker-compose logs backend`
- `docker-compose exec -T backend python manage.py test`
- `rg "catalog_service|CatalogService" library tests`

Posible solucion:

- crear o restaurar el modulo `library/catalog_service.py`
- revisar si falta tambien la ruta `/api/catalog/search/` asociada a esa funcionalidad
- ajustar o eliminar los tests si esa funcionalidad ya no forma parte del proyecto

### Respuestas finales

`¿Has podido ejecutar el proyecto sin modificar nada?`

No. Ha sido necesario anadir la configuracion de Docker Compose y Dev Containers para poder abrir y reproducir el entorno de forma consistente.

`¿Que ventajas aporta el uso de Dev Containers en un equipo de desarrollo?`

- todos los desarrolladores trabajan con el mismo entorno
- se reducen los errores de "en mi maquina funciona"
- la incorporacion de nuevos miembros es mas rapida
- las extensiones, dependencias y puertos pueden quedar definidos en el proyecto
- mejora la reproducibilidad del desarrollo y las pruebas
