import uuid
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from vendors.models import VendorBusiness, VendorGalleryCategory, VendorGalleryEvent, VendorGallery

User = get_user_model()


class VendorAPITest(APITestCase):
    def setUp(self):
        # Create vendor user
        self.vendor_user = User.objects.create_user(
            username="test_vendor",
            email="vendor@example.com",
            password="Password123!",
            role=User.Role.VENDOR,
            is_email_verified=True,
            onboarding_status=User.OnboardingStatus.ACTIVE
        )
        # Create business profile
        self.business = VendorBusiness.objects.create(
            user=self.vendor_user,
            business_name="Magic Studio",
            address="123 Visual St",
            email="magic@example.com",
            phone_number="+2348000000000",
            custom_url="magic-studio"
        )
        # Create category
        self.category = VendorGalleryCategory.objects.create(
            vendor=self.business,
            name="Weddings",
            description="Wedding photography"
        )
        # Create category event
        self.gallery_event = VendorGalleryEvent.objects.create(
            category=self.category,
            name="Alice & Bob's Wedding",
            description="Beautiful wedding photos",
            location="Lagos, Nigeria"
        )

    def test_vendor_business_detail_and_update(self):
        self.client.force_authenticate(user=self.vendor_user)
        url = reverse("vendors:business-detail")
        
        # Get business details
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "Magic Studio")

        # Update business details
        payload = {"business_name": "Magic Visual Studio"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.business.refresh_from_db()
        self.assertEqual(self.business.business_name, "Magic Visual Studio")

    def test_category_list_create(self):
        self.client.force_authenticate(user=self.vendor_user)
        url = reverse("vendors:category-list-create")

        # List categories
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Create category
        payload = {"name": "Corporate Events", "description": "Corporate events photos"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VendorGalleryCategory.objects.filter(name="Corporate Events").exists())

    def test_category_detail_update_delete(self):
        self.client.force_authenticate(user=self.vendor_user)
        url = reverse("vendors:category-detail", kwargs={"pk": self.category.id})

        # Get details
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update category
        payload = {"name": "Pre-Weddings"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Pre-Weddings")

        # Delete category
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VendorGalleryCategory.objects.filter(id=self.category.id).exists())

    def test_event_list_create(self):
        self.client.force_authenticate(user=self.vendor_user)
        url = reverse("vendors:event-list-create")

        # List events
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Create event
        payload = {
            "category": str(self.category.id),
            "name": "Annual General Meeting",
            "description": "AGM coverage",
            "location": "Lagos"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VendorGalleryEvent.objects.filter(name="Annual General Meeting").exists())

    def test_event_detail_update_delete(self):
        self.client.force_authenticate(user=self.vendor_user)
        url = reverse("vendors:event-detail", kwargs={"pk": self.gallery_event.id})

        # Get details
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update event
        payload = {"name": "Alice & Bob - Day 2"}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.gallery_event.refresh_from_db()
        self.assertEqual(self.gallery_event.name, "Alice & Bob - Day 2")

        # Delete event
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VendorGalleryEvent.objects.filter(id=self.gallery_event.id).exists())

    def test_vendor_public_profile_lookup(self):
        # Lookup by UUID
        url = reverse("vendors:public-profile", kwargs={"lookup": str(self.business.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "Magic Studio")

        # Lookup by custom slug URL
        url = reverse("vendors:public-profile", kwargs={"lookup": "magic-studio"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["business_name"], "Magic Studio")
