import requests
from celery import shared_task
from django.conf import settings
from .models.photo import Photo, UserPhoto
from accounts.models.user import User

FASTAPI_PROCESS_BATCH_URL = "http://localhost:8002/process-batch"

@shared_task
def extract_faces_from_photos(photo_ids):
    """
    Sends a batch of photo_ids to FastAPI microservice.
    """
    photos = Photo.objects.filter(id__in=photo_ids, ai_status=Photo.AIProcessingStatus.PENDING)
    if not photos.exists():
        return
        
    # We assume all photos in the batch belong to the same event
    event_id = str(photos.first().event_id)
    valid_photo_ids = [str(photo.id) for photo in photos]
    
    try:
        payload = {
            'photo_ids': valid_photo_ids,
            'event_id': event_id
        }
        
        response = requests.post(FASTAPI_PROCESS_BATCH_URL, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to trigger batch classifier: {response.text}")
            photos.update(ai_status=Photo.AIProcessingStatus.FAILED)
            
    except Exception as e:
        print(f"Failed to trigger batch classifier: {e}")
        photos.update(ai_status=Photo.AIProcessingStatus.FAILED)


@shared_task
def notify_users_of_mapped_gallery(event_id):
    """
    Finds all users who have matched photos for the event and sends them an email.
    """
    user_ids = UserPhoto.objects.filter(event_id=event_id).values_list('user_id', flat=True).distinct()
    users = User.objects.filter(id__in=user_ids)
    
    if not users.exists():
        return "No users to notify."
        
    for user in users:
        gallery_url = f"https://neoevents.com/events/{event_id}/gallery?category=personal"
        
        from django.core.mail import send_mail
        
        subject = "Your Event Photos are Ready!"
        message = f"Hello {user.first_name},\n\nWe found some great photos of you! Check them out and download your personalized gallery here:\n{gallery_url}"
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email to {user.email}: {e}")
            
    return f"Sent notifications to {users.count()} attendees."
