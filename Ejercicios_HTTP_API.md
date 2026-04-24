# Ejercicios HTTP y API

## Ejercicio 1: metodos HTTP

En este proyecto los metodos HTTP indican la intencion de cada peticion. No se eligen al azar: el backend usa el metodo para saber si debe leer datos, crear algo, sustituirlo, modificar solo una parte o borrarlo.

### GET

`GET` se usa para consultar informacion sin modificarla.

Ejemplos del proyecto:

- `GET /api/health/`: comprueba que la API responde.
- `GET /api/users/me/`: devuelve el usuario autenticado.
- `GET /api/library/entries/`: lista las entradas de biblioteca del usuario.
- `GET /api/library/entries/{id}/`: devuelve una entrada concreta si pertenece al usuario.

Es correcto usar `GET` aqui porque el servidor no cambia ningun dato.

### POST

`POST` se usa cuando la peticion provoca una accion o crea un recurso nuevo.

Ejemplos del proyecto:

- `POST /api/auth/register/`: crea un usuario.
- `POST /api/auth/login/`: inicia sesion.
- `POST /api/auth/logout/`: cierra la sesion.
- `POST /api/users/me/password/`: cambia la contrasena del usuario autenticado.
- `POST /api/library/entries/`: crea una entrada nueva en la biblioteca.

No seria correcto usar `GET` para estos casos porque cambian el estado del servidor: se crea un usuario, se abre/cierra sesion o se modifica una contrasena.

### PUT

`PUT` se usa para sustituir completamente un recurso existente.

Ejemplo del proyecto:

- `PUT /api/library/entries/{id}/`: reemplaza todos los datos editables de una entrada: `external_game_id`, `status` y `hours_played`.

En este endpoint se exige el JSON completo. Si falta un campo, la peticion no representa una sustitucion completa y se devuelve `400`.

### PATCH

`PATCH` se usa para actualizar solo una parte de un recurso.

Ejemplo del proyecto:

- `PATCH /api/library/entries/{id}/`: permite cambiar solo `status`, solo `hours_played` o ambos.

Es distinto de `PUT` porque no obliga a enviar todos los campos. Si solo quiero cambiar el estado de `wishlist` a `playing`, `PATCH` es el metodo mas adecuado.

### DELETE

`DELETE` se usa para eliminar un recurso.

Ejemplo del proyecto:

- `DELETE /api/users/me/`: borra la cuenta del usuario autenticado.

Al borrar el usuario tambien se eliminan sus entradas de biblioteca, porque el modelo `LibraryEntry` tiene una relacion con el usuario usando `on_delete=models.CASCADE`.

## Ejercicio 1: codigos de estado

### 200 OK

Significa que la peticion se ha procesado correctamente y hay respuesta con contenido.

Aparece en:

- `GET /api/health/`
- `POST /api/auth/login/`
- `GET /api/users/me/`
- `GET /api/library/entries/`
- `GET /api/library/entries/{id}/`
- `PATCH /api/library/entries/{id}/`
- `PUT /api/library/entries/{id}/`
- `POST /api/users/me/password/`

Ejemplo: al cambiar la contrasena correctamente se devuelve `200` con:

```json
{ "ok": true }
```

### 201 Created

Significa que se ha creado un recurso nuevo.

Aparece en:

- `POST /api/auth/register/`: crea un usuario.
- `POST /api/library/entries/`: crea una entrada de biblioteca.

### 204 No Content

Significa que la accion ha ido bien, pero no hay nada que devolver en el cuerpo.

Aparece en:

- `POST /api/auth/logout/`: cierra la sesion y devuelve body vacio.
- `DELETE /api/users/me/`: borra la cuenta y devuelve body vacio.

### 400 Bad Request

Significa que el cliente ha enviado datos incorrectos, incompletos o con formato no valido.

Aparece en:

- Registro con password corta o usuario duplicado.
- Login sin `password`.
- Crear una entrada sin campos obligatorios.
- Crear o actualizar una entrada con `status` no permitido.
- `PATCH` con un campo desconocido.
- `PUT` sin algun campo obligatorio.
- Cambiar contrasena con contrasena actual incorrecta, nueva contrasena corta o JSON vacio.

El formato usado es `validation_error` cuando el problema es de validacion.

### 401 Unauthorized

Significa que la peticion necesita autenticacion y el usuario no ha iniciado sesion, o que las credenciales no son validas.

Aparece en:

- `GET /api/users/me/` sin sesion.
- `POST /api/library/entries/` sin sesion.
- `GET`, `PATCH` o `PUT /api/library/entries/{id}/` sin sesion.
- `POST /api/users/me/password/` sin sesion.
- `DELETE /api/users/me/` sin sesion.
- `POST /api/auth/login/` con usuario o contrasena incorrectos.

### 403 Forbidden

Significa que el servidor sabe quien eres, pero no te permite hacer esa accion.

En este proyecto no se devuelve `403` de forma explicita. Para entradas de biblioteca ajenas se devuelve `404`, no `403`, para no revelar si existe una entrada de otro usuario.

### 404 Not Found

Significa que el recurso solicitado no existe para ese usuario.

Aparece en:

- `GET /api/library/entries/{id}/` si la entrada no existe.
- `GET /api/library/entries/{id}/` si la entrada existe pero pertenece a otro usuario.
- `PATCH /api/library/entries/{id}/` con una entrada inexistente o ajena.
- `PUT /api/library/entries/{id}/` con una entrada inexistente o ajena.

Usar `404` para recursos ajenos es una decision de seguridad: el usuario no puede distinguir entre "no existe" y "existe, pero no es mio".

### 409 Conflict

Significa que la peticion entra en conflicto con el estado actual del servidor, por ejemplo crear un recurso duplicado.

En este proyecto no se usa `409`. Cuando un usuario intenta crear o cambiar una entrada para que repita `external_game_id`, el backend mantiene el formato de semanas anteriores y devuelve `400` con:

```json
{
  "error": "duplicate_entry",
  "message": "El juego ya existe en la biblioteca",
  "details": { "external_game_id": "duplicate" }
}
```

Un `409` tambien seria defendible para duplicados, pero se ha mantenido `400` para no romper la API existente.

### 500 Internal Server Error

Significa que ha fallado el servidor por un error no controlado.

No es una respuesta que el backend devuelva a proposito. La API valida los casos esperados para responder con `400`, `401` o `404` antes de que se conviertan en errores internos.

## Ejercicio 2: cambio de contrasena

Ruta implementada:

```text
POST /api/users/me/password/
```

El frontend debe enviar:

```json
{
  "current_password": "password123",
  "new_password": "newpass123"
}
```

El backend comprueba:

- Que el usuario esta autenticado.
- Que el JSON es valido y no esta vacio.
- Que existen `current_password` y `new_password`.
- Que los dos campos son cadenas de texto.
- Que `current_password` coincide con la contrasena real del usuario.
- Que `new_password` tiene al menos 8 caracteres.

Si todo va bien, guarda la nueva contrasena usando `set_password`, por lo que nunca se guarda ni se devuelve en texto plano.

Respuesta correcta:

```json
{ "ok": true }
```

Codigo: `200`.

Errores:

- Sin autenticar: `401` con `unauthorized`.
- Contrasena actual incorrecta: `400` con `validation_error`.
- Nueva contrasena corta: `400` con `validation_error`.
- JSON vacio: `400` con `validation_error`.

## Ejercicio 3: limpieza interna

Se ha refactorizado el backend sin cambiar las rutas ni los formatos JSON:

- `library/api_helpers.py`: respuestas comunes, parseo de JSON, comprobacion de autenticacion y serializadores.
- `library/validators.py`: validaciones de usuarios, login, contrasena y entradas de biblioteca.
- `library/views.py`: queda centrado en el flujo de cada endpoint.
- Se han anadido comentarios breves en estas partes para explicar que hace cada bloque principal.

Con esto se evita repetir logica como construir errores, validar campos o convertir modelos a JSON. Las rutas siguen devolviendo los mismos codigos y estructuras.

## Ejercicio 4: PUT de entrada de biblioteca

Ruta implementada:

```text
PUT /api/library/entries/{id}/
```

El JSON debe ser completo:

```json
{
  "external_game_id": "game-2",
  "status": "playing",
  "hours_played": 12
}
```

Comportamiento:

- Sin autenticar: `401`.
- Entrada inexistente o de otro usuario: `404`.
- Falta algun campo: `400`.
- Campo con tipo incorrecto: `400`.
- `status` no permitido: `400`.
- `hours_played` negativo: `400`.
- Duplicado de `external_game_id` para el mismo usuario: `400` con `duplicate_entry`.
- Todo correcto: `200` con el recurso actualizado.

## Ejercicio 5: analisis de PATCH

Endpoint analizado:

```text
PATCH /api/library/entries/{id}/
```

El metodo `PATCH` es adecuado porque no sustituye toda la entrada, solo modifica algunos campos. En este proyecto permite cambiar `status`, `hours_played` o ambos. Si el objetivo fuese reemplazar tambien `external_game_id` y exigir todos los campos, seria mejor `PUT`.

Es correcto que el backend compruebe el usuario que hace la peticion. Una entrada de biblioteca pertenece a un usuario concreto, asi que no basta con recibir el `id`: hay que buscar con `pk=entry_id` y `user=request.user`. De esa forma un usuario no puede modificar entradas de otra cuenta.

Los codigos son coherentes:

- `200`: actualizacion parcial correcta.
- `400`: JSON vacio, campo desconocido o dato invalido.
- `401`: usuario no autenticado.
- `404`: entrada inexistente o perteneciente a otro usuario.

Casos contemplados:

- `status` debe ser uno de los estados permitidos.
- `hours_played` debe ser entero y no negativo.
- Los campos desconocidos se rechazan.
- Las entradas ajenas se tratan como no encontradas.

No cambiaria el metodo ni los codigos actuales. Si en el futuro se permitiera modificar `external_game_id` con `PATCH`, habria que anadir la comprobacion de duplicados igual que en `POST` y `PUT`.

## Ejercicio 6: logout

Ruta implementada:

```text
POST /api/auth/logout/
```

No necesita body.

Devuelve siempre:

```text
204 No Content
```

El body va vacio tanto si habia usuario autenticado como si no. Esto hace que cerrar sesion sea idempotente: llamar a logout varias veces deja el sistema en el mismo estado, con el usuario no autenticado.

## Ejercicio 7: borrar cuenta

Ruta implementada:

```text
DELETE /api/users/me/
```

Comportamiento:

- Si el usuario no esta autenticado, devuelve `401` con `unauthorized`.
- Si esta autenticado, borra su propia cuenta y devuelve `204` con body vacio.

No hay parametro de usuario en la URL. Esto es importante porque evita que un usuario indique el id de otra cuenta. La ruta siempre actua sobre `request.user`.

Al borrar el usuario tambien se eliminan sus entradas de biblioteca por la relacion:

```python
on_delete=models.CASCADE
```

## Pruebas realizadas

Se han anadido pruebas para:

- Cambio correcto de contrasena.
- Cambio de contrasena con contrasena actual incorrecta.
- Cambio de contrasena con nueva contrasena corta.
- Cambio de contrasena con JSON vacio.
- Cambio de contrasena sin autenticar.
- `PUT` correcto.
- `PUT` con datos invalidos.
- `PUT` sin autenticar.
- `PUT` sobre entrada inexistente o ajena.
- Logout despues de login.
- Logout sin autenticar.
- Borrado de cuenta autenticado.
- Borrado de cuenta sin autenticar.

Comando ejecutado:

```bash
python manage.py test
```

Resultado:

```text
Found 394 test(s).
Ran 394 tests.
OK
```

## Guion breve para clase

La idea principal es que cada metodo HTTP expresa una intencion: `GET` consulta, `POST` crea o ejecuta acciones, `PUT` reemplaza todo, `PATCH` modifica una parte y `DELETE` elimina. En la API las rutas siempre comprueban autenticacion cuando trabajan con datos privados. Para la biblioteca se filtra por `user=request.user`, asi que un usuario solo ve y modifica sus propias entradas. Los errores tambien siguen una logica: `400` para datos mal enviados, `401` para falta de sesion, `404` para recursos que no existen o no pertenecen al usuario, `201` cuando se crea algo y `204` cuando la accion funciona pero no hay contenido que devolver.
