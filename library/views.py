import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import LibraryEntry


ALLOWED_STATUSES = {
    LibraryEntry.STATUS_WISHLIST,
    LibraryEntry.STATUS_PLAYING,
    LibraryEntry.STATUS_COMPLETED,
    LibraryEntry.STATUS_DROPPED,
}


def validation_error(details=None):
    body = {
        "error": "validation_error",
        "message": "Datos de entrada inválidos",
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


def validate_create_payload(data):
    details = {}

    if "external_game_id" not in data:
        details["external_game_id"] = "required"
    elif type(data["external_game_id"]) is not str:
        details["external_game_id"] = "must_be_string"

    if "status" not in data:
        details["status"] = "required"
    elif type(data["status"]) is not str:
        details["status"] = "must_be_string"
    elif data["status"] not in ALLOWED_STATUSES:
        details["status"] = "invalid_choice"

    if "hours_played" not in data:
        details["hours_played"] = "required"
    elif type(data["hours_played"]) is not int:
        details["hours_played"] = "must_be_integer"
    elif data["hours_played"] < 0:
        details["hours_played"] = "must_be_greater_or_equal_to_0"

    return details


def validate_patch_payload(data):
    details = {}
    allowed_fields = {"status", "hours_played"}

    for field in data:
        if field not in allowed_fields:
            details[field] = "unknown_field"

    if "status" in data:
        if type(data["status"]) is not str:
            details["status"] = "must_be_string"
        elif data["status"] not in ALLOWED_STATUSES:
            details["status"] = "invalid_choice"

    if "hours_played" in data:
        if type(data["hours_played"]) is not int:
            details["hours_played"] = "must_be_integer"
        elif data["hours_played"] < 0:
            details["hours_played"] = "must_be_greater_or_equal_to_0"

    return details


def serialize_entry(entry):
    return {
        "id": entry.id,
        "external_game_id": entry.external_game_id,
        "status": entry.status,
        "hours_played": entry.hours_played,
    }


@csrf_exempt
def entries(request):
    if request.method == "POST":
        data, error_response = parse_json_body(request)
        if error_response is not None:
            return error_response

        details = validate_create_payload(data)
        if details:
            return validation_error(details)

        if LibraryEntry.objects.filter(external_game_id=data["external_game_id"]).exists():
            return duplicate_error()

        entry = LibraryEntry.objects.create(
            external_game_id=data["external_game_id"],
            status=data["status"],
            hours_played=data["hours_played"],
        )
        return JsonResponse(serialize_entry(entry), status=201)

    if request.method == "GET":
        payload = [serialize_entry(entry) for entry in LibraryEntry.objects.order_by("id")]
        return JsonResponse(payload, safe=False, status=200)

    return JsonResponse({"error": "method_not_allowed"}, status=405)


@csrf_exempt
def entry_detail(request, entry_id):
    try:
        entry = LibraryEntry.objects.get(pk=entry_id)
    except LibraryEntry.DoesNotExist:
        return not_found_error()

    if request.method == "GET":
        return JsonResponse(serialize_entry(entry), status=200)

    if request.method == "PATCH":
        data, error_response = parse_json_body(request)
        if error_response is not None:
            return error_response

        details = validate_patch_payload(data)
        if details:
            return validation_error(details)

        if "status" in data:
            entry.status = data["status"]
        if "hours_played" in data:
            entry.hours_played = data["hours_played"]
        entry.save(update_fields=list(data.keys()))
        return JsonResponse(serialize_entry(entry), status=200)

    return JsonResponse({"error": "method_not_allowed"}, status=405)
