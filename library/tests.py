import json

from django.test import TestCase

from .models import LibraryEntry


class LibraryApiTests(TestCase):
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

    def test_create_entry_success(self):
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

    def test_create_entry_rejects_empty_json(self):
        response = self.post_json("/api/library/entries/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_create_entry_rejects_invalid_status_type(self):
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
                "message": "Datos de entrada inválidos",
                "details": {"body": "invalid_json"},
            },
        )

    def test_duplicate_entry_returns_expected_error(self):
        self.post_json(
            "/api/library/entries/",
            {
                "external_game_id": "game-1",
                "status": "wishlist",
                "hours_played": 0,
            },
        )

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

    def test_list_entries_returns_expected_fields(self):
        LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )
        LibraryEntry.objects.create(
            external_game_id="game-2",
            status="playing",
            hours_played=8,
        )

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

    def test_detail_returns_expected_fields(self):
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

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

    def test_detail_returns_not_found_error(self):
        response = self.client.get("/api/library/entries/999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "error": "not_found",
                "message": "La entrada solicitada no existe",
            },
        )

    def test_patch_updates_entry(self):
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

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
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

        response = self.patch_json(f"/api/library/entries/{entry.id}/", {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_patch_rejects_invalid_status(self):
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"status": "paused"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"status": "invalid_choice"})

    def test_patch_rejects_negative_hours(self):
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

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
        entry = LibraryEntry.objects.create(
            external_game_id="game-1",
            status="wishlist",
            hours_played=0,
        )

        response = self.patch_json(
            f"/api/library/entries/{entry.id}/",
            {"title": "New title"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["details"], {"title": "unknown_field"})

    def test_patch_returns_not_found_error(self):
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
