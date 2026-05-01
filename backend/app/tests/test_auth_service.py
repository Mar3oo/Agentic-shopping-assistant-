import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.services.auth_service import (
    get_current_user,
    hash_password,
    login_user,
    register_user,
    verify_password,
)


class PasswordHashingTests(unittest.TestCase):
    def test_hash_and_verify_password_round_trip(self):
        stored_hash = hash_password("StrongPass123")
        self.assertTrue(stored_hash.startswith("scrypt$"))
        self.assertTrue(verify_password("StrongPass123", stored_hash))
        self.assertFalse(verify_password("WrongPass123", stored_hash))


class RegisterUserTests(unittest.TestCase):
    @patch("backend.app.services.auth_service.create_registered_user")
    @patch("backend.app.services.auth_service.get_user_by_email")
    def test_register_user_returns_registered_payload(
        self,
        mock_get_user_by_email,
        mock_create_registered_user,
    ):
        mock_get_user_by_email.return_value = None
        mock_create_registered_user.return_value = {
            "user_id": "user_123",
            "mode": "registered",
            "email": "user@example.com",
            "display_name": "Ayman",
        }

        response = register_user("User@example.com", "StrongPass123", "Ayman")

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["user_id"], "user_123")
        self.assertEqual(response["data"]["mode"], "registered")
        self.assertEqual(response["data"]["email"], "user@example.com")
        self.assertNotEqual(mock_create_registered_user.call_args.kwargs["password_hash"], "StrongPass123")

    @patch("backend.app.services.auth_service.get_user_by_email")
    def test_register_user_rejects_duplicate_email(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = {"user_id": "user_existing"}

        with self.assertRaises(HTTPException) as context:
            register_user("user@example.com", "StrongPass123")

        self.assertEqual(context.exception.status_code, 409)


class LoginUserTests(unittest.TestCase):
    @patch("backend.app.services.auth_service.update_last_seen")
    @patch("backend.app.services.auth_service.get_user_by_email")
    def test_login_user_returns_existing_user_identity(
        self,
        mock_get_user_by_email,
        mock_update_last_seen,
    ):
        stored_hash = hash_password("StrongPass123")
        mock_get_user_by_email.return_value = {
            "user_id": "user_123",
            "mode": "registered",
            "email": "user@example.com",
            "display_name": "Ayman",
            "password_hash": stored_hash,
            "is_active": True,
        }
        mock_update_last_seen.return_value = {
            "user_id": "user_123",
            "mode": "registered",
            "email": "user@example.com",
            "display_name": "Ayman",
            "is_active": True,
        }

        response = login_user("user@example.com", "StrongPass123")

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["user_id"], "user_123")

    @patch("backend.app.services.auth_service.get_user_by_email")
    def test_login_user_rejects_bad_password(self, mock_get_user_by_email):
        mock_get_user_by_email.return_value = {
            "user_id": "user_123",
            "mode": "registered",
            "email": "user@example.com",
            "password_hash": hash_password("StrongPass123"),
            "is_active": True,
        }

        with self.assertRaises(HTTPException) as context:
            login_user("user@example.com", "WrongPass123")

        self.assertEqual(context.exception.status_code, 401)


class GetCurrentUserTests(unittest.TestCase):
    @patch("backend.app.services.auth_service.get_user")
    def test_get_current_user_returns_user_payload(self, mock_get_user):
        mock_get_user.return_value = {
            "user_id": "user_123",
            "mode": "registered",
            "email": "user@example.com",
            "display_name": "Ayman",
            "is_active": True,
        }

        response = get_current_user("user_123")

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
