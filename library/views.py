import json

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as django_login,
    logout as django_logout,
    update_session_auth_hash,
)
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import LibraryEntry
from .validators import (
    validate_create_payload,
    validate_login_payload,
    validate_password_change_payload,
    validate_patch_payload,
    validate_put_payload,
)


def validation_error(details=None):
    body = {
        "error": "validation_error",
        "message": "Datos de entrada inv\u00e1lidos",
    }
    if details is not None:
        body["details"] = details
    return JsonResponse(body, status=400)


def duplicate_error():
    return JsonResponse(
        {
            "error": "duplicate_entry",
            "message": "El juego ya existe en la biblioteca",
            "details": {"external_game_id": "duplicate"},
        },
        status=400,
    )


def not_found_error():
    return JsonResponse(
        {
            "error": "not_found",
            "message": "La entrada solicitada no existe",
        },
        status=404,
    )


def unauthorized_error(message):
    return JsonResponse(
        {
            "error": "unauthorized",
            "message": message,
        },
        status=401,
    )


def method_not_allowed():
    return JsonResponse({"error": "method_not_allowed"}, status=405)


def require_authenticated(request):
    if not request.user.is_authenticated:
        return unauthorized_error("No autenticado")
    return None


def parse_json_body(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, validation_error({"body": "invalid_json"})

    if not isinstance(data, dict):
        return None, validation_error({"body": "invalid_format"})
    if not data:
        return None, validation_error({"body": "empty"})
    return data, None


def validate_register_payload(data):
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


def serialize_entry(entry):
    return {
        "id": entry.id,
        "external_game_id": entry.external_game_id,
        "status": entry.status,
        "hours_played": entry.hours_played,
    }


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
    }


def message_response(message, status=200):
    return JsonResponse({"message": message}, status=status)


def health(request):
    if request.method != "GET":
        return method_not_allowed()

    return JsonResponse({"status": "ok"}, status=200)


@csrf_exempt
def register(request):
    if request.method != "POST":
        return method_not_allowed()

    data, error_response = parse_json_body(request)
    if error_response is not None:
        return error_response

    details = validate_register_payload(data)
    if details:
        return validation_error(details)

    User = get_user_model()
    user = User.objects.create_user(
        username=data["username"],
        password=data["password"],
    )
    return JsonResponse(serialize_user(user), status=201)


@csrf_exempt
def login(request):
    if request.method != "POST":
        return method_not_allowed()

    data, error_response = parse_json_body(request)
    if error_response is not None:
        return error_response

    details = validate_login_payload(data)
    if details:
        return validation_error(details)

    user = authenticate(
        request,
        username=data["username"],
        password=data["password"],
    )
    if user is None:
        return unauthorized_error("Credenciales incorrectas")

    django_login(request, user)
    return JsonResponse(serialize_user(user), status=200)


@csrf_exempt
def logout(request):
    if request.method != "POST":
        return method_not_allowed()

    django_logout(request)
    return message_response("Sesion cerrada")


def me(request):
    if request.method == "PUT":
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    if request.method != "GET":
        return method_not_allowed()

    return JsonResponse(serialize_user(request.user), status=200)


@csrf_exempt
def change_password(request):
    if request.method != "POST":
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    data, error_response = parse_json_body(request)
    if error_response is not None:
        return error_response

    details = validate_password_change_payload(data, request.user)
    if details:
        return validation_error(details)

    request.user.set_password(data["new_password"])
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return message_response("Contrasena actualizada")


@csrf_exempt
def entries(request):
    if request.method not in {"POST", "GET"}:
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    if request.method == "POST":
        data, error_response = parse_json_body(request)
        if error_response is not None:
            return error_response

        details = validate_create_payload(data)
        if details:
            return validation_error(details)

        if LibraryEntry.objects.filter(
            user=request.user,
            external_game_id=data["external_game_id"],
        ).exists():
            return duplicate_error()

        try:
            entry = LibraryEntry.objects.create(
                user=request.user,
                external_game_id=data["external_game_id"],
                status=data["status"],
                hours_played=data["hours_played"],
            )
        except IntegrityError:
            return duplicate_error()

        return JsonResponse(serialize_entry(entry), status=201)

    payload = [
        serialize_entry(entry)
        for entry in LibraryEntry.objects.filter(user=request.user).order_by("id")
    ]
    return JsonResponse(payload, safe=False, status=200)


@csrf_exempt
def entry_detail(request, entry_id):
    if request.method not in {"GET", "PATCH", "PUT"}:
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    try:
        entry = LibraryEntry.objects.get(pk=entry_id, user=request.user)
    except LibraryEntry.DoesNotExist:
        return not_found_error()

    if request.method == "GET":
        return JsonResponse(serialize_entry(entry), status=200)

    data, error_response = parse_json_body(request)
    if error_response is not None:
        return error_response

    if request.method == "PUT":
        details = validate_put_payload(data)
    else:
        details = validate_patch_payload(data)
    if details:
        return validation_error(details)

    update_fields = []
    if request.method == "PUT":
        entry.external_game_id = data["external_game_id"]
        entry.status = data["status"]
        entry.hours_played = data["hours_played"]
        update_fields = ["external_game_id", "status", "hours_played"]
    else:
        if "status" in data:
            entry.status = data["status"]
            update_fields.append("status")
        if "hours_played" in data:
            entry.hours_played = data["hours_played"]
            update_fields.append("hours_played")

    entry.save(update_fields=update_fields)
    return JsonResponse(serialize_entry(entry), status=200)
