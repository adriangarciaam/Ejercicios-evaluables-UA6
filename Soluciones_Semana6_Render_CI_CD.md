# Soluciones Semana 6 - CI/CD con Render

## Ejercicio 1

### Flujo actual del pipeline

El pipeline actual esta definido en `.github/workflows/ci.yml`.

Su flujo queda asi:

1. `Checkout repository`
2. `Set up Python`
3. `Install dependencies`
4. `Run backend tests`

### Donde se ejecutan los tests

Los tests se ejecutan en el job `test`, en el paso:

```yaml
- name: Run backend tests
  run: python manage.py test
```

### Donde se comprueba que el proyecto esta en un estado correcto

La comprobacion real del estado del proyecto ocurre al final del job `test`, cuando:

- ya se ha descargado el codigo,
- ya se ha preparado el entorno,
- ya se han instalado las dependencias,
- y los tests del backend terminan correctamente.

Si ese job falla, el proyecto no se considera valido para desplegar.

### En que punto debe añadirse el despliegue

El despliegue debe añadirse despues del job de tests, no antes.

En GitHub Actions eso significa crear un segundo job con:

- `needs: test`
- ejecucion solo en `main`

### Por que ese es el momento adecuado

Ese es el punto correcto porque el despliegue solo debe lanzarse cuando el codigo:

- compila e instala dependencias sin errores,
- pasa la validacion automatica,
- y pertenece a la rama principal que actua como rama de entrega.

Si se desplegara antes de los tests, o sin depender del job `test`, Render podria publicar una version rota.

## Ejercicio 2

### Configuracion aplicada en GitHub Actions

El workflow se ha ampliado para incluir un job `deploy`:

- depende de `test`
- solo se ejecuta en eventos `push`
- solo se ejecuta en `refs/heads/main`
- llama al Deploy Hook de Render mediante `curl`

Fragmento relevante:

```yaml
deploy:
  needs: test
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

### Secreto necesario en GitHub

En el repositorio de GitHub debes crear el secreto:

```text
RENDER_DEPLOY_HOOK_URL
```

Valor:

- la URL del Deploy Hook del servicio web en Render

Ruta en GitHub:

- `Settings > Secrets and variables > Actions > New repository secret`

### Configuracion que debes dejar en Render

1. Conectar el repositorio de GitHub al servicio web.
2. Asegurar que la rama vinculada del servicio es `main`.
3. Copiar el `Deploy Hook` desde `Settings`.

Recomendacion practica:

- dejar el auto deploy nativo de Render en `Off` si vas a disparar el despliegue desde GitHub Actions con el hook

Motivo:

- evita despliegues duplicados para el mismo commit

### Comportamiento esperado tras un commit en `main`

Cuando hagas un commit y `push` a `main`:

1. GitHub Actions ejecuta el job `test`
2. si `test` acaba en verde, se ejecuta el job `deploy`
3. el job `deploy` llama al hook de Render
4. Render arranca un nuevo despliegue automaticamente

## Ejercicio 3

### Relacion entre CI y despliegue

La relacion queda definida por `needs: test`.

Eso significa:

- si `test` falla, `deploy` no se ejecuta
- si `test` pasa, `deploy` si puede ejecutarse

Ademas, el despliegue solo ocurre en `main`, por la condicion:

```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

### Resultado esperado

Caso 1:

- el CI falla
- el job `deploy` no se lanza
- en Render no aparece un nuevo despliegue provocado por ese commit

Caso 2:

- el CI pasa
- el job `deploy` se ejecuta
- Render recibe el hook y crea un nuevo deploy

### Explicacion breve

El CI actua como puerta de seguridad del despliegue.

Render no debe recibir la orden de desplegar hasta que GitHub Actions confirme que el backend esta correcto. Por eso el despliegue no depende solo del commit, sino del resultado satisfactorio del pipeline.

## Estado local verificado

Comando ejecutado:

```bash
python manage.py test
```

Resultado:

```text
Found 151 test(s).
System check identified no issues (0 silenced).
Ran 151 tests in 45.340s
OK
```

## Pendiente de hacer en tu cuenta

No puedo completar desde local estas acciones porque dependen de tu panel de Render y de GitHub:

1. crear el secreto `RENDER_DEPLOY_HOOK_URL`
2. copiar la URL real del Deploy Hook desde Render
3. hacer `push` de este workflow a `main`
4. sacar las capturas de GitHub Actions y Render

## Capturas que debes entregar

Para el ejercicio 2:

- configuracion del servicio en Render con el repositorio conectado y el hook disponible
- deploy lanzado automaticamente tras un commit correcto

Para el ejercicio 3:

- ejecucion con CI fallido donde no se dispare despliegue
- ejecucion con CI correcto y despliegue completado en Render
