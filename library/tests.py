import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import LibraryEntry


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

    def login_as(self, user=None):
        self.client.force_login(user or self.user)

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

    def test_register_success(self):
        response = self.post_json(
            "/api/auth/register/",
            {"username": "carla", "password": "password123"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["username"], "carla")
        self.assertIn("id", response.json())
        self.assertNotIn("password", response.json())

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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

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
