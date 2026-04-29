from django.contrib.auth import get_user_model

from .models import LibraryEntry


ALLOWED_STATUSES = {
    LibraryEntry.STATUS_WISHLIST,
    LibraryEntry.STATUS_PLAYING,
    LibraryEntry.STATUS_COMPLETED,
    LibraryEntry.STATUS_DROPPED,
}

ENTRY_FULL_FIELDS = {"external_game_id", "status", "hours_played"}
ENTRY_PATCH_FIELDS = {"status", "hours_played"}


def validate_external_game_id(data, details, required):
    # Comprueba presencia y tipo del identificador externo del juego.
    if "external_game_id" not in data:
        if required:
            details["external_game_id"] = "required"
    elif type(data["external_game_id"]) is not str:
        details["external_game_id"] = "must_be_string"


def validate_status(data, details, required):
    # Valida que el estado exista y sea uno de los permitidos.
    if "status" not in data:
        if required:
            details["status"] = "required"
    elif type(data["status"]) is not str:
        details["status"] = "must_be_string"
    elif data["status"] not in ALLOWED_STATUSES:
        details["status"] = "invalid_choice"


def validate_hours_played(data, details, required):
    # Asegura que las horas sean un entero positivo o cero.
    if "hours_played" not in data:
        if required:
            details["hours_played"] = "required"
    elif type(data["hours_played"]) is not int:
        details["hours_played"] = "must_be_integer"
    elif data["hours_played"] < 0:
        details["hours_played"] = "must_be_greater_or_equal_to_0"


def validate_unknown_fields(data, details, allowed_fields):
    # Rechaza campos que la API no permite modificar.
    for field in data:
        if field not in allowed_fields:
            details[field] = "unknown_field"


def validate_entry_payload(data, *, required, allowed_fields):
    # Agrupa las reglas comunes de POST, PUT y PATCH de biblioteca.
    details = {}

    validate_unknown_fields(data, details, allowed_fields)
    validate_external_game_id(data, details, required)
    validate_status(data, details, required)
    validate_hours_played(data, details, required)

    return details


def validate_create_payload(data):
    # POST necesita todos los campos obligatorios de una entrada nueva.
    details = {}

    validate_external_game_id(data, details, required=True)
    validate_status(data, details, required=True)
    validate_hours_played(data, details, required=True)

    return details


def validate_put_payload(data):
    # PUT sustituye la entrada completa, por eso exige todos los campos.
    return validate_entry_payload(
        data,
        required=True,
        allowed_fields=ENTRY_FULL_FIELDS,
    )


def validate_patch_payload(data):
    # PATCH permite actualizar solo status y/o hours_played.
    return validate_entry_payload(
        data,
        required=False,
        allowed_fields=ENTRY_PATCH_FIELDS,
    )


def validate_register_payload(data):
    # Valida el alta y evita usuarios duplicados o passwords cortas.
    details = {}
    User = get_user_model()

    if "username" not in data:
        details["username"] = "required"
    elif type(data["username"]) is not str:
        details["username"] = "must_be_string"
    elif User.objects.filter(username=data["username"]).exists():
        details["username"] = "duplicate"

    if "password" not in data:
        details["password"] = "required"
    elif type(data["password"]) is not str:
        details["password"] = "must_be_string"
    elif len(data["password"]) < 8:
        details["password"] = "min_length_8"

    return details


def validate_catalog_search_query(query):
    # El buscador requiere un texto no vacio.
    if not isinstance(query, str) or not query.strip():
        return {"q": "required"}
    return {}


def validate_catalog_resolve_payload(data):
    # Resolve exige una lista no vacia de identificadores externos.
    details = {}
    values = data.get("external_game_ids")

    if values is None:
        details["external_game_ids"] = "required"
        return details
    if type(values) is not list:
        details["external_game_ids"] = "must_be_array"
        return details
    if not values:
        details["external_game_ids"] = "required"
        return details

    for value in values:
        if type(value) is not str:
            details["external_game_ids"] = "must_be_array_of_strings"
            return details
        if not value.strip():
            details["external_game_ids"] = "must_be_array_of_strings"
            return details

    return details


def validate_login_payload(data):
    # Login solo necesita username y password como cadenas.
    details = {}

    if "username" not in data:
        details["username"] = "required"
    elif type(data["username"]) is not str:
        details["username"] = "must_be_string"

    if "password" not in data:
        details["password"] = "required"
    elif type(data["password"]) is not str:
        details["password"] = "must_be_string"

    return details


def validate_password_change_payload(data, user):
    # Comprueba password actual y longitud minima de la nueva.
    details = {}

    if "current_password" not in data:
        details["current_password"] = "required"
    elif type(data["current_password"]) is not str:
        details["current_password"] = "must_be_string"
    elif not user.check_password(data["current_password"]):
        details["current_password"] = "incorrect"

    if "new_password" not in data:
        details["new_password"] = "required"
    elif type(data["new_password"]) is not str:
        details["new_password"] = "must_be_string"
    elif len(data["new_password"]) < 8:
        details["new_password"] = "min_length_8"

    return details
