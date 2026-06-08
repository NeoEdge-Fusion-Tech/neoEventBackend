import requests
from celery import shared_task
from django.conf import settings
from decouple import config
from .models.photo import Photo, UserPhoto
from accounts.models.user import User

FASTAPI_PROCESS_BATCH_URL = config("FASTAPI_PROCESS_BATCH_URL", default="http://localhost:8002/process-batch")

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


import logging

logger = logging.getLogger(__name__)

@shared_task
def notify_users_of_mapped_gallery(event_id):
    """
    Finds all users who have matched photos for the event and sends them an email.
    """
    user_ids = UserPhoto.objects.filter(event_id=event_id).values_list('user_id', flat=True).distinct()
    users = User.objects.filter(id__in=user_ids)
    
    if not users.exists():
        return "No users to notify."
        
    from events.models.event import Event
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found when trying to send emails.")
        return "Event not found."
        
    for user in users:
        # Dynamically use the frontend URL from settings instead of hardcoding
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        gallery_url = f"{frontend_url}/events/{event_id}/gallery?category=personal"
        
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        subject = f"Your Photos from {event.title} are Ready!"
        
        # Render the HTML template
        html_content = render_to_string("emails/gallery_ready.html", {
            "user": user,
            "event": event,
            "gallery_url": gallery_url,
            "frontend_url": frontend_url
        })
        
        # Create plain-text fallback
        text_content = strip_tags(html_content)
        
        try:
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            # We fail silently but log the actual error so it can be detected in CloudWatch/Logs
            logger.error(f"Failed to send gallery notification email to {user.email} for event {event_id}: {e}", exc_info=True)
            
    return f"Sent notifications to {users.count()} attendees."
