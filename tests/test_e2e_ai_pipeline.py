import os
import sys
import time
import requests
import urllib.request
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from accounts.models import User
from events.models import Event
from tickets.models import EventRegistration
from photos.models.photo import Photo, UserPhoto
from classifier_service.tasks import task_run_attendee_scan, task_generate_embeddings

def download_image(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
    return filename

def run_e2e_test():
    print("=== Starting E2E AI Pipeline Test ===")
    
    # 1. Download sample face images
    selfie_path = download_image("https://raw.githubusercontent.com/deepinsight/insightface/master/sample-images/t1.jpg", "test_selfie.jpg")
    group_photo_path = download_image("https://raw.githubusercontent.com/deepinsight/insightface/master/sample-images/t1.jpg", "test_group.jpg")
    
    # 2. Setup Database Mocks
    user_email = "test_ai_attendee@example.com"
    owner_email = "test_ai_owner@example.com"
    
    # Cleanup previous runs
    User.objects.filter(email=user_email).delete()
    User.objects.filter(email=owner_email).delete()
    Event.objects.filter(title="AI Test Event").delete()

    print("Creating Test Users and Event...")
    attendee = User.objects.create_user(
        email=user_email, username="test_ai_attendee", password="password123", role="ATTENDEE"
    )
    
    owner = User.objects.create_user(
        email=owner_email, username="test_ai_owner", password="password123", role="OWNER"
    )

    event = Event.objects.create(
        title="AI Test Event",
        description="Testing AI Pipeline",
        creator=owner
    )
    
    attendee_profile = attendee.attendee_profile
    
    registration = EventRegistration.objects.create(
        event=event,
        attendee=attendee_profile,
    )

    # 3. Upload Selfie and Trigger Scan
    print("Uploading Selfie and triggering Attendee Scan...")
    # Read the selfie image
    with open(selfie_path, 'rb') as f:
        selfie_data = f.read()
    
    # Normally this is triggered via an API endpoint, but we can call the Celery task directly for E2E
    # We will save the selfie to the attendee's profile
    attendee.reference_image.save('selfie.jpg', SimpleUploadedFile('selfie.jpg', selfie_data))
    attendee.save()

    # Create a local copy to use for the temp_selfie_path
    with open('temp_selfie.jpg', 'wb') as f:
        f.write(selfie_data)

    scan_result = task_run_attendee_scan(attendee.id, 'temp_selfie.jpg')
    print(f"Attendee Scan Task Result: {scan_result}")

    # 4. Upload Event Photo
    print("Uploading Event Photo...")
    with open(group_photo_path, 'rb') as f:
        group_photo_data = f.read()

    photo = Photo.objects.create(
        event=event,
        uploader=owner,
        media_file=SimpleUploadedFile('group.jpg', group_photo_data)
    )

    # 5. Trigger Photo Embedding Generation
    print("Triggering Photo Embedding Task...")
    photo_result = task_generate_embeddings(photo.id)
    print(f"Photo Embedding Task Result: {photo_result}")

    # Give Celery/FastAPI some time to process if it's asynchronous
    print("Waiting for AI processing (5 seconds)...")
    time.sleep(5)

    # 6. Validate Results
    print("Validating Matches in DB...")
    user_photos = UserPhoto.objects.filter(user=attendee, event=event)
    
    if user_photos.exists():
        print(f"SUCCESS: Found {user_photos.count()} matches for the Attendee!")
        for up in user_photos:
            print(f" - Matched Photo ID: {up.photo.id}, Confidence: {up.confidence_score}")
    else:
        print("FAILED: No matches found for the Attendee in the uploaded event photos.")
        print("Checking Photo ai_status...")
        photo.refresh_from_db()
        print(f"Photo AI Status: {photo.ai_status}")

    print("=== Test Complete ===")

if __name__ == "__main__":
    run_e2e_test()
