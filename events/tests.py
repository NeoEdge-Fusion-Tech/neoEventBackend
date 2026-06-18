import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from events.models import Event, EventVendor

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# 1. Event Model Tests
# ──────────────────────────────────────────────────────────────────────────────
class EventModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER
        )

    def test_slug_generation_on_save(self):
        event = Event.objects.create(
            owner=self.owner,
            title="My Awesome Event",
            description="Testing slug",
            venue_name="Main Hall",
            venue_address="123 Test St",
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=3),
            registration_deadline=timezone.now() + timedelta(days=1),
        )
        self.assertTrue(event.slug.startswith("my-awesome-event-"))
        self.assertEqual(str(event), "My Awesome Event")

    def test_is_live_property(self):
        event = Event.objects.create(
            owner=self.owner,
            title="Live Event Test",
            description="Testing live property",
            venue_name="Main Hall",
            venue_address="123 Test St",
            start_date=timezone.now() - timedelta(hours=2),
            end_date=timezone.now() + timedelta(hours=2),
            registration_deadline=timezone.now() - timedelta(hours=3),
            status=Event.Status.ACTIVE
        )
        self.assertTrue(event.is_live)

        # Draft is not live
        event.status = Event.Status.DRAFT
        event.save()
        self.assertFalse(event.is_live)

    def test_can_register_property(self):
        event = Event.objects.create(
            owner=self.owner,
            title="Registration Test",
            description="Testing registration property",
            venue_name="Main Hall",
            venue_address="123 Test St",
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=3),
            registration_deadline=timezone.now() + timedelta(days=1),
            status=Event.Status.PUBLISHED
        )
        self.assertTrue(event.can_register)

        # Past deadline cannot register
        event.registration_deadline = timezone.now() - timedelta(hours=1)
        event.save()
        self.assertFalse(event.can_register)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Event API View Tests
# ──────────────────────────────────────────────────────────────────────────────
class EventAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.attendee = User.objects.create_user(
            username="attendee_user",
            email="attendee@example.com",
            password="Password123!",
            role=User.Role.ATTENDEE,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.event = Event.objects.create(
            owner=self.owner,
            title="Conference 2026",
            description="Annual Conference",
            venue_name="Convention Center",
            venue_address="Downtown",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            registration_deadline=timezone.now() + timedelta(days=4),
            status=Event.Status.PUBLISHED,
            is_public=True
        )

    def test_list_public_events(self):
        url = reverse("event-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_event_detail_by_slug(self):
        url = reverse("event-detail", kwargs={"slug": self.event.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Conference 2026")

    def test_get_event_detail_by_uuid(self):
        url = reverse("event-detail", kwargs={"slug": str(self.event.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Conference 2026")

    def test_create_event_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-create")
        payload = {
            "title": "New Tech Meetup",
            "description": "Discussing Python 3.14",
            "venue_name": "Hub Room",
            "venue_address": "456 Tech Lane",
            "start_date": (timezone.now() + timedelta(days=10)).isoformat(),
            "end_date": (timezone.now() + timedelta(days=11)).isoformat(),
            "registration_deadline": (timezone.now() + timedelta(days=8)).isoformat(),
            "max_participants": 50,
            "status": "DRAFT",
            "is_public": True,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Event.objects.filter(title="New Tech Meetup").exists())

    def test_create_event_fails_for_non_owner(self):
        self.client.force_authenticate(user=self.attendee)
        url = reverse("event-create")
        payload = {
            "title": "Hackathon",
            "description": "Code all night",
            "venue_name": "Lab",
            "venue_address": "University",
            "start_date": (timezone.now() + timedelta(days=1)).isoformat(),
            "end_date": (timezone.now() + timedelta(days=2)).isoformat(),
            "registration_deadline": (timezone.now() + timedelta(hours=12)).isoformat(),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_event_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-update", kwargs={"id": self.event.id})
        payload = {"title": "Updated Conference Title"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Conference Title")

    def test_delete_event_by_owner(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-delete", kwargs={"id": self.event.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_event_forbidden_for_non_owner(self):
        self.client.force_authenticate(user=self.attendee)
        url = reverse("event-delete", kwargs={"id": self.event.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())

    def test_owner_only_sees_own_events_in_my_events(self):
        other_owner = User.objects.create_user(
            username="other_owner",
            email="other_owner@example.com",
            password="Password123!",
            role=User.Role.OWNER,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        Event.objects.create(
            owner=other_owner,
            title="Other Owner's Event",
            description="Should not be visible to self.owner",
            venue_name="Somewhere",
            venue_address="Elsewhere",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            registration_deadline=timezone.now() + timedelta(days=4),
            status=Event.Status.DRAFT,
            is_public=False,
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-list-mine")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [e["title"] for e in response.data["results"]]
        self.assertEqual(titles, ["Conference 2026"])

    def test_admin_sees_all_events_in_my_events(self):
        admin = User.objects.create_user(
            username="super_admin",
            email="admin@example.com",
            password="Password123!",
            role=User.Role.ADMIN,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.client.force_authenticate(user=admin)
        url = reverse("event-list-mine")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_non_owner_forbidden_from_my_events(self):
        self.client.force_authenticate(user=self.attendee)
        url = reverse("event-list-mine")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_public_event_hidden_from_others(self):
        self.event.is_public = False
        self.event.save()

        url = reverse("event-detail", kwargs={"slug": self.event.slug})
        anon_response = self.client.get(url)
        self.assertEqual(anon_response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=self.attendee)
        attendee_response = self.client.get(url)
        self.assertEqual(attendee_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_public_event_visible_to_owner_and_admin(self):
        self.event.is_public = False
        self.event.save()
        admin = User.objects.create_user(
            username="super_admin2",
            email="admin2@example.com",
            password="Password123!",
            role=User.Role.ADMIN,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        url = reverse("event-detail", kwargs={"slug": self.event.slug})

        self.client.force_authenticate(user=self.owner)
        owner_response = self.client.get(url)
        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=admin)
        admin_response = self.client.get(url)
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)

    def test_admin_can_update_and_delete_others_event(self):
        admin = User.objects.create_user(
            username="super_admin3",
            email="admin3@example.com",
            password="Password123!",
            role=User.Role.ADMIN,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.client.force_authenticate(user=admin)

        update_url = reverse("event-update", kwargs={"id": self.event.id})
        response = self.client.patch(update_url, {"title": "Admin Edited Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Admin Edited Title")

        delete_url = reverse("event-delete", kwargs={"id": self.event.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())


    def test_generate_presigned_url_endpoint(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-generate-presigned-url")
        payload = {
            "files": [
                {"file_name": "banner.jpg", "file_type": "image/jpeg"},
                {"file_name": "flyer.png", "file_type": "image/png"}
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("urls", response.data)
        self.assertEqual(len(response.data["urls"]), 2)
        self.assertEqual(response.data["urls"][0]["original_name"], "banner.jpg")
        self.assertIn("presigned_url", response.data["urls"][0])
        self.assertIn("full_url", response.data["urls"][0])

    def test_create_event_with_presigned_urls(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-create")
        payload = {
            "title": "Presigned Event Test",
            "description": "Testing with presigned URLs",
            "venue_name": "Virtual Room",
            "venue_address": "https://zoom.us",
            "start_date": (timezone.now() + timedelta(days=10)).isoformat(),
            "end_date": (timezone.now() + timedelta(days=11)).isoformat(),
            "registration_deadline": (timezone.now() + timedelta(days=8)).isoformat(),
            "max_participants": 100,
            "status": "DRAFT",
            "is_public": True,
            "banner_image": "https://neo-events.s3.amazonaws.com/media/event_banners/abc-123_banner.jpg",
            "banner_portrait": "https://neo-events.s3.amazonaws.com/media/event_banners/xyz-789_portrait.png",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(title="Presigned Event Test")
        self.assertEqual(event.banner_image.name, "event_banners/abc-123_banner.jpg")
        self.assertEqual(event.banner_portrait.name, "event_banners/xyz-789_portrait.png")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Vendor Assignment & Invitation Tests
# ──────────────────────────────────────────────────────────────────────────────
class EventVendorAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=User.Role.OWNER,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        self.vendor_user = User.objects.create_user(
            username="vendor_user",
            email="vendor@example.com",
            password="Password123!",
            role=User.Role.VENDOR,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        # Create profile for validator dynamically or vendor
        from accounts.models import VendorProfile
        VendorProfile.objects.create(
            user=self.vendor_user,
            subtype="PHOTOGRAPHER"
        )
        self.event = Event.objects.create(
            owner=self.owner,
            title="Music Festival",
            description="Loud sounds",
            venue_name="Park",
            venue_address="Outdoors",
            start_date=timezone.now() + timedelta(days=5),
            end_date=timezone.now() + timedelta(days=6),
            registration_deadline=timezone.now() + timedelta(days=4),
            status=Event.Status.PUBLISHED,
        )

    def test_list_event_vendors(self):
        EventVendor.objects.create(
            event=self.event,
            vendor=self.vendor_user,
            role=EventVendor.VendorRole.PHOTOGRAPHER,
            is_confirmed=True
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-vendor-list", kwargs={"event_id": self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("events.services.emails.notify")
    def test_invite_vendor(self, mock_notify):
        mock_notify.send.return_value = {"email": True}
        self.client.force_authenticate(user=self.owner)
        url = reverse("event-vendor-invite", kwargs={"event_id": self.event.id})
        payload = {
            "vendor_email": "newvendor@example.com",
            "vendor_name": "New Photographer",
            "vendor_phone": "+2348000000001",
            "role": "PHOTOGRAPHER",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EventVendor.objects.filter(invited_email="newvendor@example.com").exists())

    def test_remove_vendor(self):
        assignment = EventVendor.objects.create(
            event=self.event,
            vendor=self.vendor_user,
            role=EventVendor.VendorRole.PHOTOGRAPHER
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            "event-vendor-remove",
            kwargs={"event_id": self.event.id, "vendor_assignment_id": assignment.id}
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(EventVendor.objects.filter(id=assignment.id).exists())

    def test_vendor_respond_to_invite_accept(self):
        invitation_code = uuid.uuid4()
        assignment = EventVendor.objects.create(
            event=self.event,
            invited_email=self.vendor_user.email,
            role=EventVendor.VendorRole.PHOTOGRAPHER,
            invitation_code=invitation_code,
            is_confirmed=False
        )
        url = reverse("vendor-respond-invite", kwargs={"invitation_code": str(invitation_code)})
        payload = {"accept": True}
        self.client.force_authenticate(user=self.vendor_user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_confirmed)
        self.assertEqual(assignment.vendor, self.vendor_user)

    def test_vendor_setup_password_for_new_account(self):
        invitation_code = uuid.uuid4()
        assignment = EventVendor.objects.create(
            event=self.event,
            invited_email="unregistered@example.com",
            role=EventVendor.VendorRole.PLANNER,
            invitation_code=invitation_code,
            is_confirmed=False
        )
        url = reverse("vendor-setup-password", kwargs={"invitation_code": str(invitation_code)})
        payload = {
            "password": "VendorNewPass123!",
            "password_confirm": "VendorNewPass123!",
            "business_name": "Sparkle Planners",
            "address": "45 Sparkle Road",
            "vendor_subtype": "PLANNER"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="unregistered@example.com").exists())
        new_user = User.objects.get(email="unregistered@example.com")
        self.assertEqual(new_user.role, User.Role.VENDOR)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Validator API Tests
# ──────────────────────────────────────────────────────────────────────────────
class ValidatorAPITest(APITestCase):
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
        self.event = Event.objects.create(
            owner=self.owner,
            title="Football Match",
            description="Stadium event",
            venue_name="Stadium",
            venue_address="East Side",
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            registration_deadline=timezone.now() + timedelta(hours=12),
            status=Event.Status.ACTIVE,
        )

    def test_validator_onboard_endpoint(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("validator-onboard")
        payload = {
            "device_name": "Main Entrance Scanner",
            "is_active": True,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validator_login_endpoint(self):
        url = reverse("validator-login")
        payload = {
            "username": "val@example.com",
            "password": "Password123!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_validator_event_list(self):
        self.client.force_authenticate(user=self.validator_user)
        url = reverse("validator-event-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
