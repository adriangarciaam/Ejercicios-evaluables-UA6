import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, override_settings

from .api_helpers import (
    external_service_error,
    external_service_unavailable_error,
    invalid_external_game_id_error,
)
from .catalog import CatalogResponseError, CatalogUnavailableError
from .models import LibraryEntry


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LibraryApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.password = "password123"
        self.user = User.objects.create_user(
            username="ana",
            password=self.password,
        )
        self.other_user = User.objects.create_user(
            username="bea",
            password=self.password,
        )
        self.catalog_validation_patcher = patch(
            "library.views.validate_external_game_id_in_catalog",
            return_value=None,
        )
        self.mock_validate_external_game_id_in_catalog = (
            self.catalog_validation_patcher.start()
        )
        self.addCleanup(self.catalog_validation_patcher.stop)

    def post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def patch_json(self, url, payload):
        return self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def put_json(self, url, payload):
        return self.client.put(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def login_as(self, user=None):
        self.client.force_login(user or self.user)

    def assert_json_content_type(self, response):
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def assert_validation_error(self, response, details):
        self.assertEqual(response.status_code, 400)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            {
                "error": "validation_error",
                "message": "Datos de entrada inv\u00e1lidos",
                "details": details,
            },
        )

    def assert_method_not_allowed(self, response):
        self.assertEqual(response.status_code, 405)
        self.assert_json_content_type(response)
        self.assertEqual(response.json(), {"error": "method_not_allowed"})

    def assert_external_service_unavailable(self, response):
        self.assertEqual(response.status_code, 503)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            {
                "error": "external_service_unavailable",
                "message": "El cat\u00e1logo externo no est\u00e1 disponible. Int\u00e9ntalo m\u00e1s tarde.",
            },
        )

    def assert_external_service_error(self, response):
        self.assertEqual(response.status_code, 502)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            {
                "error": "external_service_error",
                "message": "Error al consultar el cat\u00e1logo externo.",
            },
        )

    def assert_invalid_external_game_id(self, response):
        self.assertEqual(response.status_code, 400)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            {
                "error": "invalid_external_game_id",
                "message": "El juego indicado no existe en el cat\u00e1logo externo.",
                "details": {"external_game_id": "not_found"},
            },
        )

    def create_entry(
        self,
        external_game_id="game-1",
        status="wishlist",
        hours_played=0,
        user=None,
    ):
        return LibraryEntry.objects.create(
            user=user or self.user,
            external_game_id=external_game_id,
            status=status,
            hours_played=hours_played,
        )

    def test_frontend_home_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 201)
        self.assertContains(response, "Biblioteca de videojuegos")

    def test_register_success(self):
        response = self.post_json(
            "/api/auth/register/",
            {"username": "carla", "password": "password123"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "carla")
        self.assertIn("id", response.json())
        self.assertNotIn("password", response.json())

    def test_register_rejects_get_method(self):
        response = self.client.get("/api/auth/register/")

        self.assert_method_not_allowed(response)

    def test_register_rejects_non_object_json(self):
        response = self.post_json("/api/auth/register/", ["ana", "password123"])

        self.assert_validation_error(response, {"body": "invalid_format"})

    def test_register_rejects_duplicate_username(self):
        response = self.post_json(
            "/api/auth/register/",
            {"username": "ana", "password": "password123"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"username": "duplicate"})

    def test_register_rejects_short_password(self):
        response = self.post_json(
            "/api/auth/register/",
            {"username": "carla", "password": "short"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"password": "min_length_8"})

    def test_register_rejects_invalid_types(self):
        response = self.post_json(
            "/api/auth/register/",
            {"username": 10, "password": []},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["details"],
            {
                "username": "must_be_string",
                "password": "must_be_string",
            },
        )

    def test_register_rejects_missing_fields(self):
        response = self.post_json("/api/auth/register/", {"username": "carla"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"password": "required"})

    def test_register_rejects_missing_username(self):
        response = self.post_json(
            "/api/auth/register/",
            {"password": "password123"},
        )

        self.assert_validation_error(response, {"username": "required"})

    def test_register_rejects_empty_json(self):
        response = self.post_json("/api/auth/register/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": "validation_error",
                "message": "Datos de entrada inv\u00e1lidos",
                "details": {"body": "empty"},
            },
        )

    def test_login_success_sets_session(self):
        response = self.post_json(
            "/api/auth/login/",
            {"username": "ana", "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.user.id,
                "username": "ana",
            },
        )

        me_response = self.client.get("/api/users/me/")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json(), response.json())

    def test_login_rejects_get_method(self):
        response = self.client.get("/api/auth/login/")

        self.assert_method_not_allowed(response)

    def test_login_rejects_bad_credentials(self):
        response = self.post_json(
            "/api/auth/login/",
            {"username": "ana", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "error": "unauthorized",
                "message": "Credenciales incorrectas",
            },
        )

    def test_login_rejects_invalid_payload(self):
        response = self.post_json("/api/auth/login/", {"username": "ana"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"password": "required"})

    def test_login_rejects_missing_username(self):
        response = self.post_json(
            "/api/auth/login/",
            {"password": self.password},
        )

        self.assert_validation_error(response, {"username": "required"})

    def test_login_rejects_empty_json(self):
        response = self.post_json("/api/auth/login/", {})

        self.assert_validation_error(response, {"body": "empty"})

    def test_login_rejects_invalid_username_type(self):
        response = self.post_json(
            "/api/auth/login/",
            {"username": 10, "password": self.password},
        )

        self.assert_validation_error(response, {"username": "must_be_string"})

    def test_login_rejects_invalid_password_type(self):
        response = self.post_json(
            "/api/auth/login/",
            {"username": "ana", "password": []},
        )

        self.assert_validation_error(response, {"password": "must_be_string"})

    def test_logout_rejects_get_method(self):
        response = self.client.get("/api/auth/logout/")

        self.assert_method_not_allowed(response)

    def test_logout_after_login_closes_session(self):
        self.login_as()

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

        me_response = self.client.get("/api/users/me/")
        self.assertEqual(me_response.status_code, 401)
        self.assertEqual(me_response.json()["error"], "unauthorized")

    def test_logout_without_authentication_returns_no_content(self):
        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_me_requires_authentication(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "error": "unauthorized",
                "message": "No autenticado",
            },
        )

    def test_me_rejects_post_method(self):
        response = self.client.post("/api/users/me/")

        self.assert_method_not_allowed(response)

    def test_me_returns_authenticated_user(self):
        self.login_as()

        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.user.id,
                "username": "ana",
            },
        )

    def test_change_password_success(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {
                "current_password": self.password,
                "new_password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))
        self.assertFalse(self.user.check_password(self.password))

    def test_change_password_rejects_get_method(self):
        response = self.client.get("/api/users/me/password/")

        self.assert_method_not_allowed(response)

    def test_change_password_rejects_wrong_current_password(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {
                "current_password": "wrong-password",
                "new_password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"current_password": "incorrect"})

    def test_change_password_rejects_missing_current_password(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {"new_password": "newpass123"},
        )

        self.assert_validation_error(response, {"current_password": "required"})

    def test_change_password_rejects_missing_new_password(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {"current_password": self.password},
        )

        self.assert_validation_error(response, {"new_password": "required"})

    def test_change_password_rejects_invalid_field_types(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {
                "current_password": 123,
                "new_password": [],
            },
        )

        self.assert_validation_error(
            response,
            {
                "current_password": "must_be_string",
                "new_password": "must_be_string",
            },
        )

    def test_change_password_rejects_short_new_password(self):
        self.login_as()

        response = self.post_json(
            "/api/users/me/password/",
            {
                "current_password": self.password,
                "new_password": "short",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"new_password": "min_length_8"})

    def test_change_password_rejects_empty_json(self):
        self.login_as()

        response = self.post_json("/api/users/me/password/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"body": "empty"})

    def test_change_password_requires_authentication(self):
        response = self.post_json(
            "/api/users/me/password/",
            {
                "current_password": self.password,
                "new_password": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_delete_me_deletes_user_and_library_entries(self):
        self.login_as()
        self.create_entry(external_game_id="game-1", user=self.user)

        response = self.client.delete("/api/users/me/")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(get_user_model().objects.filter(username="ana").exists())
        self.assertEqual(LibraryEntry.objects.count(), 0)

        me_response = self.client.get("/api/users/me/")
        self.assertEqual(me_response.status_code, 401)

        login_response = self.post_json(
            "/api/auth/login/",
            {"username": "ana", "password": self.password},
        )
        self.assertEqual(login_response.status_code, 401)

    def test_delete_me_requires_authentication(self):
        response = self.client.delete("/api/users/me/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_entries_rejects_unsupported_method(self):
        response = self.client.delete("/api/library/entries/")

        self.assert_method_not_allowed(response)

    def test_create_entry_requires_authentication(self):
        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_create_entry_success(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "id": 1,
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": 0,
            },
        )
        self.assertEqual(LibraryEntry.objects.get().user, self.user)

    def test_create_entry_rejects_empty_json(self):
        self.login_as()

        response = self.post_json("/api/library/entries/", {})

        self.assert_validation_error(response, {"body": "empty"})

    def test_create_entry_rejects_missing_required_field(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
            },
        )

        self.assert_validation_error(response, {"hours_played": "required"})

    def test_create_entry_rejects_missing_external_game_id(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assert_validation_error(response, {"external_game_id": "required"})

    def test_create_entry_rejects_invalid_external_game_id_type(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": 123,
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assert_validation_error(response, {"external_game_id": "must_be_string"})

    def test_create_entry_rejects_missing_status(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "hours_played": 0,
            },
        )

        self.assert_validation_error(response, {"status": "required"})

    def test_create_entry_rejects_invalid_status_type(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": 10,
                "hours_played": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"status": "must_be_string"})

    def test_create_entry_rejects_invalid_status_value(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "paused",
                "hours_played": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"status": "invalid_choice"})

    def test_create_entry_rejects_invalid_hours_type(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": "a lot",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"hours_played": "must_be_integer"})

    def test_create_entry_rejects_negative_hours(self):
        self.login_as()

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": -1,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["details"],
            {"hours_played": "must_be_greater_or_equal_to_0"},
        )

    def test_create_entry_rejects_malformed_json(self):
        self.login_as()

        response = self.client.post(
            "/api/library/entries/",
            data='{"external_game_id":',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": "validation_error",
                "message": "Datos de entrada inv\u00e1lidos",
                "details": {"body": "invalid_json"},
            },
        )

    def test_duplicate_entry_returns_expected_error_for_same_user(self):
        self.login_as()
        self.create_entry(external_game_id="game-1")

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "playing",
                "hours_played": 5,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": "duplicate_entry",
                "message": "El juego ya existe en la biblioteca",
                "details": {"external_game_id": "duplicate"},
            },
        )

    def test_create_entry_returns_duplicate_if_database_unique_constraint_fails(self):
        self.login_as()

        with patch(
            "library.views.LibraryEntry.objects.create",
            side_effect=IntegrityError,
        ):
            response = self.post_json(
                "/api/library/entries/",
                {
                    "external_game_id": "game-1",
                    "status": "playing",
                    "hours_played": 5,
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "error": "duplicate_entry",
                "message": "El juego ya existe en la biblioteca",
                "details": {"external_game_id": "duplicate"},
            },
        )

    def test_same_external_game_id_is_allowed_for_different_users(self):
        self.create_entry(external_game_id="game-1", user=self.user)
        self.login_as(self.other_user)

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "playing",
                "hours_played": 5,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(LibraryEntry.objects.count(), 2)
        self.assertEqual(
            LibraryEntry.objects.get(user=self.other_user).external_game_id,
            "game-1",
        )

    def test_list_requires_authentication(self):
        response = self.client.get("/api/library/entries/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_list_entries_returns_empty_list_for_authenticated_user_without_entries(self):
        self.login_as()

        response = self.client.get("/api/library/entries/")

        self.assertEqual(response.status_code, 200)
        self.assert_json_content_type(response)
        self.assertEqual(response.json(), [])

    def test_list_entries_returns_only_authenticated_user_entries(self):
        self.login_as()
        self.create_entry(external_game_id="game-1", user=self.user)
        self.create_entry(
            external_game_id="game-2",
            status="playing",
            hours_played=8,
            user=self.user,
        )
        self.create_entry(external_game_id="other-game", user=self.other_user)

        response = self.client.get("/api/library/entries/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 1,
                    "external_game_id": "game-1",
                    "status": "wishlist",
                    "hours_played": 0,
                },
                {
                    "id": 2,
                    "external_game_id": "game-2",
                    "status": "playing",
                    "hours_played": 8,
                },
            ],
        )

    def test_created_entry_is_not_visible_to_other_user(self):
        self.login_as()
        create_response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "private-game",
                "status": "wishlist",
                "hours_played": 0,
            },
        )
        self.assertEqual(create_response.status_code, 201)

        self.login_as(self.other_user)
        list_response = self.client.get("/api/library/entries/")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json(), [])

    def test_detail_requires_authentication(self):
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "error": "unauthorized",
                "message": "No autenticado",
            },
        )

    def test_detail_rejects_unsupported_method(self):
        response = self.client.delete("/api/library/entries/1/")

        self.assert_method_not_allowed(response)

    def test_detail_returns_expected_fields_for_owner(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": entry.id,
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

    def test_detail_returns_not_found_for_missing_entry(self):
        self.login_as()

        response = self.client.get("/api/library/entries/999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_detail_returns_not_found_for_other_user_entry(self):
        self.login_as()
        entry = self.create_entry(external_game_id="other-game", user=self.other_user)

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_put_replaces_owner_entry(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": entry.id,
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        entry.refresh_from_db()
        self.assertEqual(entry.external_game_id, "game-2")
        self.assertEqual(entry.status, "playing")
        self.assertEqual(entry.hours_played, 12)

    def test_put_rejects_missing_field(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"hours_played": "required"})

    def test_put_rejects_invalid_status(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "paused",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"status": "invalid_choice"})

    def test_put_rejects_negative_hours(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": -1,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(
            response.json()["details"],
            {"hours_played": "must_be_greater_or_equal_to_0"},
        )

    def test_put_rejects_unknown_field(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
                "title": "New title",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")
        self.assertEqual(response.json()["details"], {"title": "unknown_field"})

    def test_put_rejects_duplicate_external_game_id_for_same_user(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)
        self.create_entry(external_game_id="game-2", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "duplicate_entry")

    def test_put_requires_authentication(self):
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_put_returns_not_found_for_missing_entry(self):
        self.login_as()

        response = self.put_json(
            "/api/library/entries/999/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_put_returns_not_found_for_other_user_entry(self):
        self.login_as()
        entry = self.create_entry(external_game_id="other-game", user=self.other_user)

        response = self.put_json(
            f"/api/library/entries/{entry.id}/",
            {
                "external_game_id": "game-2",
                "status": "playing",
                "hours_played": 12,
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_patch_requires_authentication(self):
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"status": "playing"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_patch_updates_owner_entry(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {
                "status": "completed",
                "hours_played": 20,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": entry.id,
                "external_game_id": "game-1",
                "status": "completed",
                "hours_played": 20,
            },
        )

    def test_patch_rejects_empty_json(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(f"/api/library/entries/{entry.id}/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_patch_rejects_invalid_status(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"status": "paused"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"status": "invalid_choice"})

    def test_patch_rejects_negative_hours(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"hours_played": -1},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["details"],
            {"hours_played": "must_be_greater_or_equal_to_0"},
        )

    def test_patch_rejects_unknown_field(self):
        self.login_as()
        entry = self.create_entry(external_game_id="game-1", user=self.user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"title": "New title"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"title": "unknown_field"})

    def test_patch_returns_not_found_for_missing_entry(self):
        self.login_as()

        response = self.patch_json(
            "/api/library/entries/999/",
            {"status": "playing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_patch_returns_not_found_for_other_user_entry(self):
        self.login_as()
        entry = self.create_entry(external_game_id="other-game", user=self.other_user)

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"status": "playing"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    @patch("library.views.search_catalog_games")
    def test_catalog_search_returns_minimal_results(self, mock_search_catalog_games):
        mock_search_catalog_games.return_value = [
            {
                "external_game_id": "612",
                "title": "LEGO Batman",
                "thumb": "https://cdn.example/batman.jpg",
            }
        ]

        response = self.client.get("/api/catalog/search/?q=mario")

        self.assertEqual(response.status_code, 200)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            [
                {
                    "external_game_id": "612",
                    "title": "LEGO Batman",
                    "thumb": "https://cdn.example/batman.jpg",
                }
            ],
        )
        mock_search_catalog_games.assert_called_once_with("mario")

    def test_catalog_search_rejects_empty_query(self):
        response = self.client.get("/api/catalog/search/?q=")

        self.assert_validation_error(response, {"q": "required"})

    def test_catalog_search_rejects_missing_query(self):
        response = self.client.get("/api/catalog/search/")

        self.assert_validation_error(response, {"q": "required"})

    @patch("library.views.search_catalog_games", side_effect=CatalogUnavailableError)
    def test_catalog_search_returns_503_when_provider_is_unavailable(self, _mock_search):
        response = self.client.get("/api/catalog/search/?q=mario")

        self.assert_external_service_unavailable(response)

    @patch("library.views.search_catalog_games", side_effect=CatalogResponseError)
    def test_catalog_search_returns_502_when_provider_response_is_invalid(self, _mock_search):
        response = self.client.get("/api/catalog/search/?q=mario")

        self.assert_external_service_error(response)

    @patch("library.views.resolve_catalog_games")
    def test_catalog_resolve_returns_minimal_results(self, mock_resolve_catalog_games):
        mock_resolve_catalog_games.return_value = [
            {
                "external_game_id": "1",
                "title": "Alpha",
                "thumb": "https://cdn.example/alpha.jpg",
            },
            {
                "external_game_id": "2",
                "title": "Beta",
                "thumb": "https://cdn.example/beta.jpg",
            },
        ]

        response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": ["1", "2"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assert_json_content_type(response)
        self.assertEqual(
            response.json(),
            [
                {
                    "external_game_id": "1",
                    "title": "Alpha",
                    "thumb": "https://cdn.example/alpha.jpg",
                },
                {
                    "external_game_id": "2",
                    "title": "Beta",
                    "thumb": "https://cdn.example/beta.jpg",
                },
            ],
        )
        mock_resolve_catalog_games.assert_called_once_with(["1", "2"])

    def test_catalog_resolve_rejects_empty_list(self):
        response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": []},
        )

        self.assert_validation_error(response, {"external_game_ids": "required"})

    def test_catalog_resolve_rejects_missing_external_game_ids(self):
        response = self.post_json("/api/catalog/resolve/", {})

        self.assert_validation_error(response, {"external_game_ids": "required"})

    def test_catalog_resolve_rejects_invalid_external_game_ids_type(self):
        response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": "1"},
        )

        self.assert_validation_error(response, {"external_game_ids": "must_be_array"})

    @patch("library.views.resolve_catalog_games", side_effect=CatalogUnavailableError)
    def test_catalog_resolve_returns_503_when_provider_is_unavailable(self, _mock_resolve):
        response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": ["1", "2"]},
        )

        self.assert_external_service_unavailable(response)

    @patch("library.views.resolve_catalog_games", side_effect=CatalogResponseError)
    def test_catalog_resolve_returns_502_when_provider_response_is_invalid(self, _mock_resolve):
        response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": ["1", "2"]},
        )

        self.assert_external_service_error(response)

    def test_create_entry_rejects_unknown_external_game_id(self):
        self.login_as()
        self.mock_validate_external_game_id_in_catalog.return_value = (
            invalid_external_game_id_error()
        )

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "999999999",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assert_invalid_external_game_id(response)

    def test_create_entry_returns_503_when_catalog_validation_has_no_response(self):
        self.login_as()
        self.mock_validate_external_game_id_in_catalog.return_value = (
            external_service_unavailable_error()
        )

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "612",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assert_external_service_unavailable(response)

    def test_create_entry_returns_502_when_catalog_validation_receives_invalid_provider_data(self):
        self.login_as()
        self.mock_validate_external_game_id_in_catalog.return_value = (
            external_service_error()
        )

        response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "612",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

        self.assert_external_service_error(response)

    @patch("library.views.resolve_catalog_games")
    @patch("library.views.search_catalog_games")
    def test_week4_full_flow_search_create_list_and_resolve(
        self,
        mock_search_catalog_games,
        mock_resolve_catalog_games,
    ):
        self.login_as()
        self.mock_validate_external_game_id_in_catalog.return_value = None
        mock_search_catalog_games.return_value = [
            {
                "external_game_id": "612",
                "title": "LEGO Batman",
                "thumb": "https://cdn.example/batman.jpg",
            }
        ]
        mock_resolve_catalog_games.return_value = [
            {
                "external_game_id": "612",
                "title": "LEGO Batman",
                "thumb": "https://cdn.example/batman.jpg",
            }
        ]

        search_response = self.client.get("/api/catalog/search/?q=mario")
        self.assertEqual(search_response.status_code, 200)
        selected_external_game_id = search_response.json()[0]["external_game_id"]

        create_response = self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": selected_external_game_id,
                "status": "wishlist",
                "hours_played": 0,
            },
        )
        self.assertEqual(create_response.status_code, 201)

        list_response = self.client.get("/api/library/entries/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            list_response.json(),
            [
                {
                    "id": 1,
                    "external_game_id": "612",
                    "status": "wishlist",
                    "hours_played": 0,
                }
            ],
        )

        resolve_response = self.post_json(
            "/api/catalog/resolve/",
            {"external_game_ids": [selected_external_game_id]},
        )
        self.assertEqual(resolve_response.status_code, 200)
        self.assertEqual(
            resolve_response.json(),
            [
                {
                    "external_game_id": "612",
                    "title": "LEGO Batman",
                    "thumb": "https://cdn.example/batman.jpg",
                }
            ],
        )
