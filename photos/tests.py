import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class LocalUploadFallbackAPITest(APITestCase):
    """
    When Cloudinary isn't configured (dev/local without credentials), the
    local-upload proxy used by the presigned-upload flow must fall back to
    local filesystem storage instead of failing with a 500.
    """

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

    @override_settings(USE_S3=False, USE_CLOUDINARY=False)
    def test_put_falls_back_to_local_storage_when_cloudinary_disabled(self):
        with override_settings(MEDIA_ROOT=self.media_root, MEDIA_URL="/media/"):
            url = reverse("local-upload", kwargs={"filepath": "event_banners/test_banner.png"})
            response = self.client.put(url, data=b"fake-image-bytes", content_type="image/png")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertIn("/media/event_banners/test_banner.png", response.data["url"])

    @override_settings(USE_S3=True)
    def test_put_disabled_when_use_s3(self):
        url = reverse("local-upload", kwargs={"filepath": "event_banners/test_banner.png"})
        response = self.client.put(url, data=b"fake-image-bytes", content_type="image/png")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
