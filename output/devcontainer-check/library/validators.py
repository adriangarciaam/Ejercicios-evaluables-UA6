from .models import LibraryEntry


ALLOWED_STATUSES = {
    LibraryEntry.STATUS_WISHLIST,
    LibraryEntry.STATUS_PLAYING,
    LibraryEntry.STATUS_COMPLETED,
    LibraryEntry.STATUS_DROPPED,
}


def _validate_external_game_id(data, details, required=True):
    if "external_game_id" not in data:
        if required:
            details["external_game_id"] = "required"
        return

    if type(data["external_game_id"]) is not str:
        details["external_game_id"] = "must_be_string"


def _validate_status(data, details, required=True):
    if "status" not in data:
        if required:
            details["status"] = "required"
        return

    if type(data["status"]) is not str:
        details["status"] = "must_be_string"
    elif data["status"] not in ALLOWED_STATUSES:
        details["status"] = "invalid_choice"


def _validate_hours_played(data, details, required=True):
    if "hours_played" not in data:
        if required:
            details["hours_played"] = "required"
        return

    if type(data["hours_played"]) is not int:
        details["hours_played"] = "must_be_integer"
    elif data["hours_played"] < 0:
        details["hours_played"] = "must_be_greater_or_equal_to_0"


def validate_create_payload(data):
    details = {}
    _validate_external_game_id(data, details)
    _validate_status(data, details)
    _validate_hours_played(data, details)
    return details


def validate_put_payload(data):
    details = {}
    allowed_fields = {"external_game_id", "status", "hours_played"}

    for field in data:
        if field not in allowed_fields:
            details[field] = "unknown_field"

    _validate_external_game_id(data, details)
    _validate_status(data, details)
    _validate_hours_played(data, details)
    return details


def validate_patch_payload(data):
    details = {}
    allowed_fields = {"status", "hours_played"}

    for field in data:
        if field not in allowed_fields:
            details[field] = "unknown_field"

    _validate_status(data, details, required=False)
    _validate_hours_played(data, details, required=False)
    return details


def validate_login_payload(data):
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


def validate_register_payload(data, user_model):
    details = {}

    if "username" not in data:
        details["username"] = "required"
    elif type(data["username"]) is not str:
        details["username"] = "must_be_string"
    elif user_model.objects.filter(username=data["username"]).exists():
        details["username"] = "duplicate"

    if "password" not in data:
        details["password"] = "required"
    elif type(data["password"]) is not str:
        details["password"] = "must_be_string"
    elif len(data["password"]) < 8:
        details["password"] = "min_length_8"

    if "email" not in data:
        details["email"] = "required"
    elif type(data["email"]) is not str:
        details["email"] = "must_be_string"
    elif "@" not in data["email"]:
        details["email"] = "invalid_format"

    return details


def validate_debug_email_payload(data):
    details = {}

    if "to" not in data:
        details["to"] = "required"
    elif type(data["to"]) is not str:
        details["to"] = "must_be_string"

    if "subject" not in data:
        details["subject"] = "required"
    elif type(data["subject"]) is not str:
        details["subject"] = "must_be_string"

    if "text" not in data:
        details["text"] = "required"
    elif type(data["text"]) is not str:
        details["text"] = "must_be_string"

    return details


def validate_password_change_payload(data, user):
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
