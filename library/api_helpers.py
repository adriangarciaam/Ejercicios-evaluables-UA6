import json

from django.http import JsonResponse


def validation_error(details=None):
    # Devuelve el formato comun para errores de validacion de entrada.
    body = {
        "error": "validation_error",
        "message": "Datos de entrada inv\u00e1lidos",
    }
    if details is not None:
        body["details"] = details
    return JsonResponse(body, status=400)


def duplicate_error():
    # Indica que el usuario ya tiene ese juego en su biblioteca.
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": {"external_game_id": "duplicate"},
        },
        status=400,
    )


def invalid_external_game_id_error():
    # El identificador externo no existe en el catalogo consultado.
    return JsonResponse(
        {
            "error": "invalid_external_game_id",
            "message": "El juego indicado no existe en el cat\u00e1logo externo.",
            "details": {"external_game_id": "not_found"},
        },
        status=400,
    )


def not_found_error():
    # Oculta si el recurso no existe o pertenece a otro usuario.
    return JsonResponse(
        {
            "error": "not_found",
            "message": "La entrada solicitada no existe",
        },
        status=404,
    )


def external_service_unavailable_error():
    # El proveedor no responde por red o timeout.
    return JsonResponse(
        {
            "error": "external_service_unavailable",
            "message": "El cat\u00e1logo externo no est\u00e1 disponible. Int\u00e9ntalo m\u00e1s tarde.",
        },
        status=503,
    )


def external_service_error():
    # El proveedor ha respondido con error o con datos invalidos.
    return JsonResponse(
        {
            "error": "external_service_error",
            "message": "Error al consultar el cat\u00e1logo externo.",
        },
        status=502,
    )


def unauthorized_error(message):
    # Respuesta comun cuando falta sesion o las credenciales no sirven.
    return JsonResponse(
        {
            "error": "unauthorized",
            "message": message,
        },
        status=401,
    )


def method_not_allowed():
    # Respuesta comun para metodos HTTP no soportados por una ruta.
    return JsonResponse({"error": "method_not_allowed"}, status=405)


def require_authenticated(request):
    # Centraliza la comprobacion de usuario autenticado.
    if not request.user.is_authenticated:
        return unauthorized_error("No autenticado")
    return None


def parse_json_body(request, *, allow_empty=False):
    # Convierte el body JSON en diccionario y rechaza formatos invalidos.
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, validation_error({"body": "invalid_json"})

    if not isinstance(data, dict):
        return None, validation_error({"body": "invalid_format"})
    if not allow_empty and not data:
        return None, validation_error({"body": "empty"})
    return data, None


def serialize_entry(entry):
    # Convierte una entrada del modelo en el JSON publico de la API.
    return {
        "id": entry.id,
        "external_game_id": entry.external_game_id,
        "status": entry.status,
        "hours_played": entry.hours_played,
    }


def serialize_user(user):
    # Devuelve solo datos publicos del usuario, nunca la contrasena.
    return {
        "id": user.id,
        "username": user.username,
    }


def serialize_catalog_game(external_game_id, title, thumb):
    # Normaliza el formato minimo que el frontend espera del catalogo.
    return {
        "external_game_id": external_game_id,
        "title": title,
        "thumb": thumb,
    }
