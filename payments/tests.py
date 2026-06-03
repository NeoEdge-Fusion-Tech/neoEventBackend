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
from tickets.models import TicketType, EventRegistration
from payments.models import PaymentTransaction

User = get_user_model()


class PaymentAPITest(APITestCase):
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
            title="Tech Meetup",
            description="Discussing tech",
            venue_name="Office",
            venue_address="Road 1",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            registration_deadline=timezone.now() + timedelta(days=4),
            status=Event.Status.ACTIVE,
        )
        # Paid ticket type
        self.paid_ticket = TicketType.objects.create(
            event=self.event,
            name="Paid Ticket",
            price=150.00,
            quantity=10
        )
        # Free ticket type
        self.free_ticket = TicketType.objects.create(
            event=self.event,
            name="Free Ticket",
            price=0.00,
            quantity=10
        )
        # Registration requiring payment
        self.registration_paid = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.paid_ticket,
            status=EventRegistration.Status.PENDING
        )
        # Free registration
        self.registration_free = EventRegistration.objects.create(
            event=self.event,
            attendee=self.attendee_profile,
            attendee_name="Jane Doe",
            attendee_email="attendee@example.com",
            ticket_type=self.free_ticket,
            status=EventRegistration.Status.PENDING
        )

    def test_initialize_payment_for_free_ticket_fails(self):
        url = reverse("payment-initialize")
        payload = {
            "registration_id": str(self.registration_free.id)
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "This registration does not require payment.")

    @patch("payments.views.get_payment_provider")
    def test_initialize_payment_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.initialize_payment.return_value = {
            "authorization_url": "https://checkout.paystack.com/fake",
            "reference": "fake_ref"
        }
        mock_get_provider.return_value = mock_provider

        url = reverse("payment-initialize")
        payload = {
            "registration_id": str(self.registration_paid.id),
            "callback_url": "https://my-app.com/callback"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("authorization_url", response.data)
        self.assertTrue(PaymentTransaction.objects.filter(registration=self.registration_paid).exists())

    @patch("payments.views.get_payment_provider")
    def test_verify_payment_success(self, mock_get_provider):
        # Create a transaction
        tx = PaymentTransaction.objects.create(
            registration=self.registration_paid,
            amount=150.00,
            reference="tx_reference_123",
            status=PaymentTransaction.Status.PENDING
        )
        mock_provider = MagicMock()
        mock_provider.verify_payment.return_value = {
            "status": "success",
            "amount": 150.00
        }
        mock_get_provider.return_value = mock_provider

        url = reverse("payment-verify")
        payload = {
            "reference": "tx_reference_123"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        # Verify registration state has been updated to CONFIRMED
        self.registration_paid.refresh_from_db()
        self.assertEqual(self.registration_paid.status, EventRegistration.Status.CONFIRMED)
