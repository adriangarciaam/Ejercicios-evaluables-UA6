# Soluciones Semana 1, 2 y 3 - Python/Django

Este documento recoge solo la parte de Python/Django de los PDF. La parte de Java queda omitida.

## Semana 1

### Ejercicio 1 - GET /api/health/

Comportamiento correcto de la vista:

- Ruta: `GET /api/health/`
- Codigo HTTP esperado: `200`
- Respuesta JSON exacta:

```json
{ "status": "ok" }
```

Este comportamiento esta protegido por `HealthViewTests.test_health_get_returns_ok_status`.

### Ejercicio 2 - Metodo HTTP incorrecto en /api/health/

Si se usa un metodo distinto de `GET`, por ejemplo `POST /api/health/`, el backend responde:

- Codigo HTTP: `405`
- Respuesta JSON:

```json
{ "error": "method_not_allowed" }
```

Este caso esta protegido por `HealthViewTests.test_health_post_returns_method_not_allowed`.

Si se cambia temporalmente la vista para devolver otro JSON, el test de `health` falla. Al restaurar el codigo original, vuelve a pasar.

### Ejercicio 3 - Metodos del modelo LibraryEntry

Comportamiento considerado correcto:

| Metodo | Caso | Resultado |
| --- | --- | --- |
| `external_id_length()` | `"abc"` | `3` |
| `external_id_length()` | `""` | `0` |
| `external_id_length()` | `None` | `0` |
| `external_id_upper()` | `"abc-123"` | `"ABC-123"` |
| `external_id_upper()` | `""` | `""` |
| `external_id_upper()` | `None` | `""` |
| `hours_played_label()` | `0` | `"none"` |
| `hours_played_label()` | `9` | `"low"` |
| `hours_played_label()` | `10` | `"high"` |
| `status_value()` | `"wishlist"` | `0` |
| `status_value()` | `"playing"` | `1` |
| `status_value()` | `"completed"` | `2` |
| `status_value()` | `"dropped"` | `3` |
| `status_value()` | estado desconocido | `-1` |

Estos casos estan cubiertos en `tests/tests_models.py`.

### Ejercicios 4, 5, 6 y 7 - Tests automaticos

Quedan cubiertos con:

- Tests de `external_id_length()`.
- Tests de `external_id_upper()`.
- Tests de `hours_played_label()`.
- Tests de `status_value()`.
- Test automatico de `GET /api/health/`.
- Test automatico de metodo no valido en `/api/health/`.

## Semana 2

### Ejercicio 1 - POST /api/library/entries/

Casos cubiertos:

- Caso valido: JSON correcto, codigo `201` y estructura exacta de respuesta.
- JSON vacio: `400 validation_error`.
- Falta de campo obligatorio: `400 validation_error`.
- Tipo incorrecto en `hours_played`: `400 validation_error`.
- Valor negativo en `hours_played`: `400 validation_error`.
- `status` fuera de los permitidos: `400 validation_error`.
- Entrada duplicada por `external_game_id`: `400 duplicate_entry`.

En los errores se comprueba codigo HTTP, respuesta JSON y contrato de error.

### Ejercicio 2 - GET /api/library/entries/

Casos cubiertos:

- Usuario autenticado sin entradas: devuelve `200` y `[]`.
- Usuario autenticado con varias entradas: devuelve `200` y una lista con los campos `id`, `external_game_id`, `status` y `hours_played`.
- Con usuarios distintos, cada usuario solo ve sus propias entradas.

### Ejercicio 3 - GET /api/library/entries/{id}/

Casos cubiertos:

- Entrada existente y propia: `200` con los datos de la entrada.
- Entrada inexistente: `404 not_found`.
- Entrada de otro usuario: `404 not_found`, para no revelar recursos ajenos.

### Ejercicio 4 - PATCH /api/library/entries/{id}/

Casos cubiertos:

- Actualizacion parcial correcta.
- Error por JSON vacio.
- Error por `status` no permitido.
- Error por `hours_played` negativo.
- Error por campo desconocido.
- Entrada inexistente: `404 not_found`.
- Entrada de otro usuario: `404 not_found`.

## Semana 3

### Ejercicio 1 - POST /api/auth/register/

Casos cubiertos:

- Registro valido: `201`, devuelve `id` y `username`, y no devuelve `password`.
- JSON vacio: `400 validation_error`.
- Falta de campos obligatorios.
- Contrasena corta.
- Username repetido.
- Tipos incorrectos.

### Ejercicio 2 - POST /api/auth/login/

Casos cubiertos:

- Login valido: `200` y sesion iniciada.
- Credenciales incorrectas: `401 unauthorized`, mensaje `"Credenciales incorrectas"`.
- Validacion: JSON vacio, campos ausentes y tipos incorrectos.

### Ejercicio 3 - GET /api/users/me/

Casos cubiertos:

- Sin autenticar: `401 unauthorized`, mensaje `"No autenticado"`.
- Tras login correcto o sesion autenticada: `200`, devuelve `id` y `username`.

### Ejercicio 4 - GET /api/library/entries/ con autenticacion

Casos cubiertos:

- Sin autenticar: `401 unauthorized`.
- Autenticado: `200`.
- Dos usuarios: cada uno ve solo sus propias entradas.

### Ejercicio 5 - GET /api/library/entries/{id}/ con autenticacion

Casos cubiertos:

- Sin autenticar: `401 unauthorized`, mensaje `"No autenticado"`.
- Autenticado y entrada propia: `200`.
- Autenticado y entrada de otra persona: `404 not_found`, mensaje `"La entrada solicitada no existe"`.

### Ejercicio 6 - POST /api/library/entries/ con autenticacion

Casos cubiertos:

- Sin autenticar: `401 unauthorized`.
- Autenticado: `201`.
- Aislamiento: lo creado por un usuario no aparece en el listado del otro.

### Ejercicio 7 - Coverage

Comando de tests ejecutado:

```bash
python manage.py test
```

Resultado:

```text
Found 394 test(s).
Ran 394 tests.
OK
```

Comandos equivalentes de coverage:

```bash
coverage run --source=library,config manage.py test
coverage report -m
coverage report -m --omit=*/tests.py,*/migrations/*,config/asgi.py,config/wsgi.py
```

Resultado global completo:

- Cobertura total: `99%`.
- Archivos con menor cobertura global:
  - `config/asgi.py`: `0%`, lineas `10-16`.
  - `config/wsgi.py`: `0%`, lineas `10-16`.
  - `library/migrations/0002_libraryentry_user_and_per_user_unique.py`: `87%`, lineas `15-19`.

Resultado centrado en codigo de aplicacion, omitiendo tests, migraciones y arranque ASGI/WSGI:

- Cobertura total: `100%`.
- `library/api_helpers.py`: `100%`.
- `library/models.py`: `100%`.
- `library/validators.py`: `100%`.
- `library/views.py`: `100%`.
- `library/urls.py`: `100%`.

Partes no cubiertas en el informe global:

- `config/asgi.py` y `config/wsgi.py`: codigo de arranque del servidor, no se ejecuta al probar vistas con el cliente de Django.
- Migracion `0002`: operaciones declarativas de migracion, normalmente no son objetivo principal de tests unitarios.

Dos zonas que priorizaria para mantener o aumentar cobertura util:

1. Flujos de autenticacion y permisos en vistas: tests de integracion para asegurar que un usuario no puede leer, crear o modificar recursos de otro.
2. Validaciones de entrada: tests de vistas y unitarios para cada nuevo campo, tipo incorrecto, valor fuera de rango y JSON mal formado.

## Cambios realizados en el proyecto

- Se ampliaron los tests de API en `library/tests.py`.
- Se amplio un caso de modelo en `tests/tests_models.py`.
- Se anadio `tests/test_extra_100.py` con 100 tests adicionales de modelo, validadores y contratos HTTP/API.
- Se anadio `tests/test_extra_200.py` con 200 tests adicionales de modelo, validadores y helpers JSON.
- Se configuro un hasher rapido solo en tests para que la suite no tarde por el coste de hashing de contrasenas.
- No se modifico ni se creo ningun archivo Java.
