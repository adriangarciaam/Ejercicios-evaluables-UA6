# Soluciones Semana 4

## Resumen

Se ha resuelto la semana 4 integrando el catalogo externo de CheapShark en el backend, sin guardar el catalogo en la base de datos local.

Cambios principales:

- Nuevo endpoint `GET /api/catalog/search/`
- Nuevo endpoint `POST /api/catalog/resolve/`
- Validacion externa de `external_game_id` al crear entradas de biblioteca
- Manejo explicito de errores `400`, `502` y `503`
- Tests del flujo completo de Semana 4

## Ejercicio 1

CheapShark se ha analizado con la documentacion publica y el resumen detallado ya esta en:

- [Ejercicio_1_CheapShark.md](./Ejercicio_1_CheapShark.md)

Puntos clave:

- Busqueda por texto: `GET https://www.cheapshark.com/api/1.0/games?title={texto}`
- Consulta multiple por ID: `GET https://www.cheapshark.com/api/1.0/games?ids={id1},{id2}`
- No requiere autenticacion ni API key
- Tiene rate limiting
- `external_game_id` pasa a guardar el `gameID` de CheapShark
- El frontend solo recibe informacion minima: `external_game_id`, `title`, `thumb`
- El catalogo no se persiste porque es externo y cambiante

## Ejercicio 2

Implementado:

```text
GET /api/catalog/search/?q=mario
```

Comportamiento:

- Valida que `q` exista y no este vacio
- Consulta CheapShark desde el backend
- Devuelve una lista estable con este formato:

```json
[
  {
    "external_game_id": "123",
    "title": "Game title",
    "thumb": "https://.."
  }
]
```

Errores:

- `400 validation_error` si `q` falta o es vacio
- `503 external_service_unavailable` si hay timeout o error de red
- `502 external_service_error` si CheapShark responde mal o con datos invalidos

## Ejercicio 3

Implementado:

```text
POST /api/catalog/resolve/
```

Body esperado:

```json
{
  "external_game_ids": ["1", "2"]
}
```

Comportamiento:

- Valida que `external_game_ids` exista, sea una lista y no este vacia
- Consulta CheapShark usando varios IDs
- Devuelve una lista con:

```json
[
  {
    "external_game_id": "123",
    "title": "Game title",
    "thumb": "https://.."
  }
]
```

Errores:

- `400 validation_error` si el body es invalido
- `503 external_service_unavailable` si el proveedor no responde
- `502 external_service_error` si el proveedor responde con error o datos rotos

## Ejercicio 4

Se han implementado los tres casos obligatorios del PDF:

### Caso A

```json
{
  "error": "external_service_unavailable",
  "message": "El catalogo externo no esta disponible. Intentalo mas tarde."
}
```

Codigo: `503`

### Caso B

```json
{
  "error": "external_service_error",
  "message": "Error al consultar el catalogo externo."
}
```

Codigo: `502`

### Caso C

```json
{
  "error": "invalid_external_game_id",
  "message": "El juego indicado no existe en el catalogo externo.",
  "details": {
    "external_game_id": "not_found"
  }
}
```

Codigo: `400`

Este ultimo se aplica durante la validacion externa al crear una entrada en:

```text
POST /api/library/entries/
```

## Ejercicio 5

El flujo completo queda cubierto:

1. `GET /api/catalog/search/?q=mario`
2. Elegir `external_game_id`
3. `POST /api/library/entries/`
4. `GET /api/library/entries/`
5. `POST /api/catalog/resolve/`

Ademas:

- La biblioteca sigue requiriendo autenticacion
- La biblioteca sigue devolviendo solo datos propios del usuario
- `resolve` aporta `title` y `thumb` sin que el frontend llame directamente a CheapShark

## Archivos principales

- [config/urls.py](./config/urls.py)
- [library/api_helpers.py](./library/api_helpers.py)
- [library/catalog.py](./library/catalog.py)
- [library/validators.py](./library/validators.py)
- [library/views.py](./library/views.py)
- [library/tests.py](./library/tests.py)

## Verificacion

Tests ejecutados:

```text
python manage.py test library tests
```

Resultado:

- `409` tests ejecutados
- `OK`
