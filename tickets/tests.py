import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from events.models import Event
from accounts.models import AttendeeProfile
from tickets.models import TicketType, EventRegistration, DailyCheckIn

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# 1. Model Properties and Methods Tests
# ──────────────────────────────────────────────────────────────────────────────
class TicketModelsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER
        )
        self.event = Event.objects.create(
            owner=self.owner,
            title="Salsa Dancing Night",
            description="Learn salsa",
            venue_name="Dance Studio",
            venue_address="Avenue 1",
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=2, hours=4),
            registration_deadline=timezone.now() + timedelta(days=1),
        )

    def test_ticket_type_remaining_property(self):
        ticket_type = TicketType.objects.create(
            event=self.event,
            name="General Admission",
            price=20.00,
            quantity=100,
            sold_count=10
        )
        self.assertEqual(ticket_type.remaining, 90)

        # Sold count exceeds quantity (edge case)
        ticket_type.sold_count = 110
        ticket_type.save()
        self.assertEqual(ticket_type.remaining, 0)


# ──────────────────────────────────────────────────────────────────────────────
# 2. View Endpoints Tests
# ──────────────────────────────────────────────────────────────────────────────
class TicketAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.attendee_user = User.objects.create_user(
            username="attendee_user",
            email="attendee@example.com",
            password="Password123!",
            role=User.Role.ATTENDEE,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.attendee_profile = AttendeeProfile.objects.create(
            user=self.attendee_user,
            email=self.attendee_user.email,
            full_name="Jane Doe"
        )
        self.event = Event.objects.create(
            owner=self.owner,
            title="Tech Summit 2026",
            description="Discussing tech innovations",
            venue_name="Expo Center",
            venue_address="West Road",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            registration_deadline=timezone.now() + timedelta(days=4),
            status=Event.Status.ACTIVE,
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="Regular Pass",
            price=50.00,
            quantity=100
        )

    def test_list_event_ticket_types(self):
        url = reverse("event-ticket-types", kwargs={"event_id": self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Regular Pass")

    @patch("tickets.services.emails.notify")
    @patch("tickets.services.qr.generate_registration_qr")
    def test_register_for_event(self, mock_qr, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.force_authenticate(user=self.attendee_user)
        url = reverse("event-register")
        payload = {
            "event": str(self.event.id),
            "ticket_type": str(self.ticket_type.id),
            "full_name": "Jane Doe",
            "email": "attendee@example.com",
            "phone_number": "+2348011112222"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EventRegistration.objects.filter(attendee_email="attendee@example.com").exists())

    @patch("tickets.services.emails.notify")
    @patch("tickets.signals.send_registration_confirmation_email")  # suppress the post_save signal's own send
    def test_confirmation_email_reads_qr_via_storage_not_path(self, mock_signal_send, mock_notify):
        """
        Remote storage backends (Cloudinary/S3) raise NotImplementedError on
        `.path` — the email service must read QR bytes via `.open()`/storage
        instead, so this must work without ever touching `.path`.
        """
        from io import BytesIO
        from tickets.services.emails import send_registration_confirmation_email

        mock_notify.send.return_value = {"email": True}
        registration = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.ticket_type,
            status=EventRegistration.Status.CONFIRMED,
        )
        registration.qr_code.name = "event_banners/fake_qr.png"

        with patch.object(registration.qr_code.storage, "open", return_value=BytesIO(b"fake-png-bytes")), \
             patch.object(registration.qr_code.storage, "path", side_effect=NotImplementedError("no path")):
            send_registration_confirmation_email(registration)

        mock_notify.send.assert_called_once()
        attachments = mock_notify.send.call_args.kwargs["attachments"]
        self.assertEqual(attachments, [(f"{registration.registration_code}.png", b"fake-png-bytes", "image/png")])

    def test_list_event_registrations_owner(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.ticket_type,
            status=EventRegistration.Status.CONFIRMED
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-registrations-list", kwargs={"event_id": self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check paginated response
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_registration_detail(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.ticket_type,
            status=EventRegistration.Status.CONFIRMED
        )
        url = reverse("registration-detail", kwargs={"registration_code": registration.registration_code})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["registration_code"], registration.registration_code)

    def test_cancel_registration(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.ticket_type,
            status=EventRegistration.Status.CONFIRMED
        )
        self.client.force_authenticate(user=self.attendee_user)
        url = reverse("cancel-registration", kwargs={"id": registration.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        registration.refresh_from_db()
        self.assertEqual(registration.status, EventRegistration.Status.CANCELLED)

    def test_my_upcoming_and_past_events(self):
        self.client.force_authenticate(user=self.attendee_user)
        
        # Test upcoming events (list)
        url = reverse("attendee-upcoming-events")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test past events history
        url = reverse("attendee-event-history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_export_registrations_csv(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-export", kwargs={"event_id": self.event.id})
        response = self.client.get(url + "?type=registrations")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], "text/csv")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Validator Ticket Verification Tests
# ──────────────────────────────────────────────────────────────────────────────
class ValidatorVerificationAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.validator_user = User.objects.create_user(
            username="validator_user",
            email="val@example.com",
            password="Password123!",
            role=User.Role.VALIDATOR,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.attendee_user = User.objects.create_user(
            username="attendee_user",
            email="attendee@example.com",
            password="Password123!",
            role=User.Role.ATTENDEE,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.attendee_profile = AttendeeProfile.objects.create(
            user=self.attendee_user,
            email=self.attendee_user.email,
            full_name="Alex Smith"
        )
        self.event = Event.objects.create(
            owner=self.owner,
            title="Expo 2026",
            description="Exhibition",
            venue_name="Concourse",
            venue_address="East Street",
            start_date=timezone.now() - timedelta(hours=2),
            end_date=timezone.now() + timedelta(days=2),
            registration_deadline=timezone.now() - timedelta(hours=4),
            status=Event.Status.ACTIVE,
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name="VIP Pass",
            price=200.00,
            quantity=50
        )
        self.registration = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Alex Smith",
            attendee_email="attendee@example.com",
            ticket_type=self.ticket_type,
            status=EventRegistration.Status.CONFIRMED
        )

    def test_validator_check_in_endpoint(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("validator-check-in")
        payload = {
            "event_id": str(self.event.id),
            "ticket_id": self.registration.registration_code,
            "device_validator_id": "Scanner_Alpha"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Validated successfully.")
        self.assertTrue(DailyCheckIn.objects.filter(registration=self.registration).exists())

    def test_validator_search_endpoint(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("validator-search")
        response = self.client.get(url + f"?q=Alex&event_id={self.event.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Alex Smith")

    def test_validator_mark_badge_printed(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("validator-mark-badge-printed")
        payload = {
            "registration_code": self.registration.registration_code
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.badge_print_count, 1)

    def test_generate_badge_html_endpoint(self):
        url = reverse("badge-html", kwargs={"registration_code": self.registration.registration_code})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response['Content-Type'].startswith("text/html"))

    def test_event_check_in_view_success(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("event-check-in", kwargs={"registration_code": self.registration.registration_code})
        payload = {
            "device_id": "Scanner_Alpha",
            "date": "2026-06-03"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Check-in successful.")
        self.assertTrue(DailyCheckIn.objects.filter(registration=self.registration, date="2026-06-03").exists())

    def test_event_check_in_view_duplicate(self):
        from datetime import datetime
        DailyCheckIn.objects.create(
            registration=self.registration,
            device_id="Scanner_Alpha",
            date=datetime.strptime("2026-06-03", "%Y-%m-%d").date()
        )
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("event-check-in", kwargs={"registration_code": self.registration.registration_code})
        payload = {
            "date": "2026-06-03"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already checked in", response.data["detail"])

    def test_event_check_in_view_invalid_date(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("event-check-in", kwargs={"registration_code": self.registration.registration_code})
        payload = {
            "date": "invalid-date-format"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid date format. Use YYYY-MM-DD.")

