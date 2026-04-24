from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as django_login,
    logout as django_logout,
    update_session_auth_hash,
)
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .api_helpers import (
    duplicate_error,
    external_service_error,
    external_service_unavailable_error,
    invalid_external_game_id_error,
    method_not_allowed,
    not_found_error,
    parse_json_body,
    require_authenticated,
    serialize_entry,
    serialize_user,
    unauthorized_error,
    validation_error,
)
from .catalog import (
    CatalogResponseError,
    CatalogUnavailableError,
    catalog_game_exists,
    resolve_catalog_games,
    search_catalog_games,
)
from .models import LibraryEntry
from .validators import (
    validate_catalog_resolve_payload,
    validate_catalog_search_query,
    validate_create_payload,
    validate_login_payload,
    validate_password_change_payload,
    validate_patch_payload,
    validate_put_payload,
    validate_register_payload,
)


def frontend(request):
    # Sirve la interfaz web sencilla incluida en la app.
    return render(request, "library/index.html")


def catalog_exception_response(error):
    # Traduce errores del proveedor externo a la API publica del proyecto.
    if isinstance(error, CatalogUnavailableError):
        return external_service_unavailable_error()
    return external_service_error()


def validate_external_game_id_in_catalog(external_game_id):
    # Comprueba que el identificador externo exista antes de guardarlo.
    try:
        exists = catalog_game_exists(external_game_id)
    except (CatalogUnavailableError, CatalogResponseError) as error:
        return catalog_exception_response(error)

    if not exists:
        return invalid_external_game_id_error()
    return None


@csrf_exempt
def health(request):
    # Endpoint minimo para comprobar que la API esta levantada.
    if request.method != "GET":
        return method_not_allowed()
    return JsonResponse({"status": "ok"}, status=200)


def get_owned_entry(user, entry_id):
    # Busca una entrada solo si pertenece al usuario autenticado.
    try:
        return LibraryEntry.objects.get(pk=entry_id, user=user)
    except LibraryEntry.DoesNotExist:
        return None


def entry_exists_for_user(user, external_game_id, excluded_entry_id=None):
    # Detecta duplicados por usuario y permite excluir la entrada actual.
    entries = LibraryEntry.objects.filter(
        user=user,
        external_game_id=external_game_id,
    )
    if excluded_entry_id is not None:
        entries = entries.exclude(pk=excluded_entry_id)
    return entries.exists()


@csrf_exempt
def register(request):
    # Crea un usuario nuevo despues de validar el JSON recibido.
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
    # Comprueba credenciales y abre sesion con cookies de Django.
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
    # Cierra la sesion; repetir logout tambien devuelve 204.
    if request.method != "POST":
        return method_not_allowed()

    django_logout(request)
    return HttpResponse(status=204)


@csrf_exempt
def me(request):
    # GET devuelve el perfil; DELETE borra la propia cuenta.
    if request.method not in {"GET", "DELETE"}:
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    if request.method == "DELETE":
        user = request.user
        django_logout(request)
        user.delete()
        return HttpResponse(status=204)

    return JsonResponse(serialize_user(request.user), status=200)


@csrf_exempt
def change_password(request):
    # Cambia la contrasena del usuario autenticado.
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
    return JsonResponse({"ok": True}, status=200)


@csrf_exempt
def entries(request):
    # GET lista la biblioteca del usuario; POST crea una entrada nueva.
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

        if entry_exists_for_user(request.user, data["external_game_id"]):
            return duplicate_error()

        catalog_error = validate_external_game_id_in_catalog(data["external_game_id"])
        if catalog_error is not None:
            return catalog_error

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
    # Gestiona consulta, sustitucion completa y actualizacion parcial.
    if request.method not in {"GET", "PATCH", "PUT"}:
        return method_not_allowed()

    auth_error = require_authenticated(request)
    if auth_error is not None:
        return auth_error

    entry = get_owned_entry(request.user, entry_id)
    if entry is None:
        return not_found_error()

    if request.method == "GET":
        return JsonResponse(serialize_entry(entry), status=200)

    data, error_response = parse_json_body(request)
    if error_response is not None:
        return error_response

    if request.method == "PUT":
        details = validate_put_payload(data)
        if details:
            return validation_error(details)

        if entry_exists_for_user(
            request.user,
            data["external_game_id"],
            excluded_entry_id=entry.id,
        ):
            return duplicate_error()

        if data["external_game_id"] != entry.external_game_id:
            catalog_error = validate_external_game_id_in_catalog(data["external_game_id"])
            if catalog_error is not None:
                return catalog_error

        entry.external_game_id = data["external_game_id"]
        entry.status = data["status"]
        entry.hours_played = data["hours_played"]
        entry.save(update_fields=["external_game_id", "status", "hours_played"])
        return JsonResponse(serialize_entry(entry), status=200)

    details = validate_patch_payload(data)
    if details:
        return validation_error(details)

    updated_fields = []
    if "status" in data:
        entry.status = data["status"]
        updated_fields.append("status")
    if "hours_played" in data:
        entry.hours_played = data["hours_played"]
        updated_fields.append("hours_played")

    entry.save(update_fields=updated_fields)
    return JsonResponse(serialize_entry(entry), status=200)


@csrf_exempt
def catalog_search(request):
    # Busca juegos por titulo en CheapShark y devuelve un formato estable.
    if request.method != "GET":
        return method_not_allowed()

    query = request.GET.get("q")
    details = validate_catalog_search_query(query)
    if details:
        return validation_error(details)

    try:
        payload = search_catalog_games(query.strip())
    except (CatalogUnavailableError, CatalogResponseError) as error:
        return catalog_exception_response(error)

    return JsonResponse(payload, safe=False, status=200)


@csrf_exempt
def catalog_resolve(request):
    # Resuelve varios IDs externos a titulo y miniatura sin persistirlos.
    if request.method != "POST":
        return method_not_allowed()

    data, error_response = parse_json_body(request, allow_empty=True)
    if error_response is not None:
        return error_response

    details = validate_catalog_resolve_payload(data)
    if details:
        return validation_error(details)

    try:
        payload = resolve_catalog_games(data["external_game_ids"])
    except (CatalogUnavailableError, CatalogResponseError) as error:
        return catalog_exception_response(error)

    return JsonResponse(payload, safe=False, status=200)
