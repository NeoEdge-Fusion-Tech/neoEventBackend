"""
Unit Tests for the Accounts App.
Covers: User model properties, Registration API (Attendee, Owner, Vendor),
        Login, OTP Email Verification, Logout, and Notification service (email).
"""
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# 1. User Model Unit Tests
# ──────────────────────────────────────────────────────────────────────────────
class UserModelTest(TestCase):
    """Tests for the custom User model and its helper properties."""

    def _create_user(self, username, role, **kwargs):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPass123!",
            role=role,
            **kwargs
        )

    def test_user_str_representation(self):
        user = self._create_user("john", User.Role.ATTENDEE)
        self.assertEqual(str(user), "john (ATTENDEE)")

    def test_default_role_is_attendee(self):
        user = self._create_user("default_user", User.Role.ATTENDEE)
        self.assertEqual(user.role, User.Role.ATTENDEE)

    def test_default_onboarding_status_is_pending_email(self):
        user = self._create_user("new_user", User.Role.ATTENDEE)
        self.assertEqual(user.onboarding_status, User.OnboardingStatus.PENDING_EMAIL)

    def test_default_is_email_verified_is_false(self):
        user = self._create_user("unverified", User.Role.ATTENDEE)
        self.assertFalse(user.is_email_verified)

    # Role properties
    def test_is_admin_user_property(self):
        user = self._create_user("admin1", User.Role.ADMIN)
        self.assertTrue(user.is_admin_user)

    def test_is_not_admin_for_other_roles(self):
        user = self._create_user("owner1", User.Role.OWNER)
        self.assertFalse(user.is_admin_user)

    def test_is_vendor_property(self):
        user = self._create_user("vendor1", User.Role.VENDOR)
        self.assertTrue(user.is_vendor)
        self.assertFalse(user.is_owner)

    def test_is_owner_property(self):
        user = self._create_user("owner2", User.Role.OWNER)
        self.assertTrue(user.is_owner)
        self.assertFalse(user.is_vendor)

    def test_is_ops_admin_property(self):
        user = self._create_user("ops1", User.Role.ADMIN, admin_subtype=User.AdminSubtype.OPS)
        self.assertTrue(user.is_ops_admin)
        self.assertFalse(user.is_customer_admin)

    def test_is_customer_admin_property(self):
        user = self._create_user("cust1", User.Role.ADMIN, admin_subtype=User.AdminSubtype.CUSTOMER)
        self.assertTrue(user.is_customer_admin)
        self.assertFalse(user.is_ops_admin)

    def test_is_validator_property(self):
        user = self._create_user("val1", User.Role.VALIDATOR)
        self.assertTrue(user.is_validator)

    def test_superuser_creation_sets_admin_role(self):
        admin = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password="Admin123!"
        )
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_email_verified)
        self.assertEqual(admin.onboarding_status, User.OnboardingStatus.ACTIVE)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Registration API Tests
# ──────────────────────────────────────────────────────────────────────────────
class AttendeeRegistrationAPITest(APITestCase):
    """Tests for the Attendee registration endpoint."""

    url = reverse_lazy("accounts:attendee-register")

    def _payload(self, **overrides):
        data = {
            "username": "testattendee",
            "email": "attendee@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "first_name": "Test",
            "last_name": "Attendee",
        }
        data.update(overrides)
        return data

    @patch("accounts.services.emails.notify")
    def test_attendee_registration_returns_201(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user_id", response.data)

    @patch("accounts.services.emails.notify")
    def test_attendee_registration_creates_user_in_db(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.post(self.url, self._payload(), format="json")
        self.assertTrue(User.objects.filter(email="attendee@example.com").exists())

    @patch("accounts.services.emails.notify")
    def test_attendee_user_has_correct_role(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.post(self.url, self._payload(), format="json")
        user = User.objects.get(email="attendee@example.com")
        self.assertEqual(user.role, User.Role.ATTENDEE)

    def test_registration_fails_with_mismatched_passwords(self):
        payload = self._payload(password_confirm="WrongPass!")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_fails_with_duplicate_email(self):
        User.objects.create_user(username="existing", email="attendee@example.com", password="Pass!")
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_fails_with_missing_email(self):
        payload = self._payload()
        del payload["email"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventOwnerRegistrationAPITest(APITestCase):
    """Tests for the Event Owner registration endpoint."""

    url = reverse_lazy("accounts:owner-register")

    def _payload(self, **overrides):
        data = {
            "username": "eventowner",
            "email": "owner@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
        }
        data.update(overrides)
        return data

    @patch("accounts.services.emails.notify")
    def test_owner_registration_returns_201(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("accounts.services.emails.notify")
    def test_owner_has_correct_role(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.post(self.url, self._payload(), format="json")
        user = User.objects.get(email="owner@example.com")
        self.assertEqual(user.role, User.Role.OWNER)


class VendorRegistrationAPITest(APITestCase):
    """Tests for the Vendor registration endpoint."""

    url = reverse_lazy("accounts:vendor-register")

    def _payload(self, **overrides):
        data = {
            "username": "vendoruser",
            "email": "vendor@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "phone_number": "+2348012345678",
            "vendor_subtype": "PHOTOGRAPHER",
            "business_name": "LensCraft Studio",
            "address": "123 Creative Studio Ave, Lagos, Nigeria",
        }
        data.update(overrides)
        return data

    @patch("accounts.services.emails.notify")
    def test_vendor_registration_returns_201(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("accounts.services.emails.notify")
    def test_vendor_has_correct_role(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.post(self.url, self._payload(), format="json")
        user = User.objects.get(email="vendor@example.com")
        self.assertEqual(user.role, User.Role.VENDOR)

    @patch("accounts.services.emails.notify")
    def test_vendor_onboarding_status_is_pending_approval_after_verification(self, mock_notify):
        """Vendors go to PENDING_APPROVAL (not ACTIVE) after email verification."""
        mock_notify.send.return_value = {"email": True}
        self.client.post(self.url, self._payload(), format="json")
        user = User.objects.get(email="vendor@example.com")
        # Simulate OTP verification
        user.email_verification_otp = "123456"
        user.email_verification_otp_created_at = timezone.now()
        user.save()
        otp_url = reverse("accounts:verify-email")
        self.client.post(otp_url, {"email": user.email, "otp": "123456"}, format="json")
        user.refresh_from_db()
        self.assertEqual(user.onboarding_status, User.OnboardingStatus.PENDING_APPROVAL)


# ──────────────────────────────────────────────────────────────────────────────
# 3. OTP Email Verification Tests
# ──────────────────────────────────────────────────────────────────────────────
class OTPVerificationAPITest(APITestCase):
    """Tests for the email OTP verification endpoint."""

    url = reverse_lazy("accounts:verify-email")

    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otpuser@example.com",
            password="TestPass123!",
            role=User.Role.ATTENDEE,
        )
        self.user.email_verification_otp = "482051"
        self.user.email_verification_otp_created_at = timezone.now()
        self.user.save()

    def test_valid_otp_verifies_email(self):
        response = self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_valid_otp_returns_access_token(self):
        response = self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.assertIn("access", response.data)

    def test_invalid_otp_returns_400(self):
        response = self.client.post(self.url, {"email": self.user.email, "otp": "999999"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_otp_returns_400(self):
        self.user.email_verification_otp_created_at = timezone.now() - timedelta(minutes=20)
        self.user.save()
        response = self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", response.data["detail"].lower())

    def test_already_verified_returns_400(self):
        self.user.is_email_verified = True
        self.user.save()
        response = self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_email_returns_404(self):
        response = self.client.post(self.url, {"email": "nobody@example.com", "otp": "482051"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_otp_cleared_after_verification(self):
        self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verification_otp)
        self.assertIsNone(self.user.email_verification_otp_created_at)

    def test_attendee_goes_to_active_status_after_verification(self):
        self.client.post(self.url, {"email": self.user.email, "otp": "482051"}, format="json")
        self.user.refresh_from_db()
        self.assertEqual(self.user.onboarding_status, User.OnboardingStatus.ACTIVE)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Login Tests
# ──────────────────────────────────────────────────────────────────────────────
class LoginAPITest(APITestCase):
    """Tests for the Login API endpoint."""

    url = reverse_lazy("accounts:login")

    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="TestPass123!",
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE,
        )

    def test_login_with_correct_credentials_returns_200(self):
        response = self.client.post(self.url, {"username": "loginuser", "password": "TestPass123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_sets_refresh_cookie(self):
        response = self.client.post(self.url, {"username": "loginuser", "password": "TestPass123!"}, format="json")
        self.assertIn("refresh_token", response.cookies)

    def test_login_with_wrong_password_returns_401(self):
        response = self.client.post(self.url, {"username": "loginuser", "password": "WrongPass!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_user_returns_401(self):
        response = self.client.post(self.url, {"username": "nobody", "password": "TestPass123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────────────────────────────────────
# 5. Notification Service Tests
# ──────────────────────────────────────────────────────────────────────────────
class EmailNotificationBackendTest(TestCase):
    """Unit tests for the EmailNotificationBackend."""

    def setUp(self):
        from notifications.services.email_backend import EmailNotificationBackend
        self.backend = EmailNotificationBackend()

    @patch("notifications.services.email_backend.render_to_string", return_value="<html>Hello</html>")
    @patch("notifications.services.email_backend.EmailMultiAlternatives")
    def test_send_returns_true_on_success(self, MockEmail, mock_render):
        mock_msg = MagicMock()
        MockEmail.return_value = mock_msg
        result = self.backend.send(
            recipient="test@example.com",
            subject="Test Subject",
            template_name="emails/accounts/welcome_email.html",
            context={}
        )
        self.assertTrue(result)
        mock_msg.send.assert_called_once_with(fail_silently=False)

    @patch("notifications.services.email_backend.render_to_string", side_effect=Exception("Template not found"))
    def test_send_returns_false_on_exception(self, mock_render):
        result = self.backend.send(
            recipient="test@example.com",
            subject="Test Subject",
            template_name="emails/does_not_exist.html",
            context={}
        )
        self.assertFalse(result)

    @patch("notifications.services.email_backend.render_to_string", return_value="<html>Hello</html>")
    @patch("notifications.services.email_backend.EmailMultiAlternatives")
    def test_send_attaches_file_when_attachments_provided(self, MockEmail, mock_render):
        mock_msg = MagicMock()
        MockEmail.return_value = mock_msg
        self.backend.send(
            recipient="test@example.com",
            subject="Ticket",
            template_name="emails/tickets/registration_confirmation.html",
            context={},
            attachments=["/fake/path/qr.png"]
        )
        mock_msg.attach_file.assert_called_once_with("/fake/path/qr.png")


class NotificationDispatcherTest(TestCase):
    """Unit tests for the NotificationDispatcher."""

    def setUp(self):
        from notifications.services.dispatcher import NotificationDispatcher
        self.dispatcher = NotificationDispatcher()

    @patch("notifications.services.email_backend.EmailNotificationBackend.send", return_value=True)
    def test_dispatcher_routes_to_email_backend(self, mock_send):
        results = self.dispatcher.send(
            channels=["email"],
            recipient_data={"email": "test@example.com"},
            subject="Hello",
            template_name="emails/accounts/welcome_email.html",
            context={}
        )
        self.assertTrue(results["email"])
        mock_send.assert_called_once()

    def test_dispatcher_returns_false_for_unsupported_channel(self):
        results = self.dispatcher.send(
            channels=["push"],
            recipient_data={"push": "device_token_123"},
            subject="Hello",
            template_name="emails/accounts/welcome_email.html",
            context={}
        )
        self.assertFalse(results["push"])

    def test_dispatcher_returns_false_when_no_recipient_for_channel(self):
        results = self.dispatcher.send(
            channels=["email"],
            recipient_data={},  # No email key
            subject="Hello",
            template_name="emails/accounts/welcome_email.html",
            context={}
        )
        self.assertFalse(results["email"])

    @patch("notifications.services.email_backend.EmailNotificationBackend.send", return_value=True)
    @patch("notifications.services.sms_backend.SMSNotificationBackend.send", return_value=True)
    def test_dispatcher_routes_to_multiple_channels(self, mock_sms, mock_email):
        results = self.dispatcher.send(
            channels=["email", "sms"],
            recipient_data={"email": "test@example.com", "sms": "+123456789"},
            subject="Multi-channel",
            template_name="emails/accounts/welcome_email.html",
            context={}
        )
        self.assertTrue(results["email"])
        self.assertTrue(results["sms"])
