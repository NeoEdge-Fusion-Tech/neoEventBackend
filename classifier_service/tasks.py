import os
import logging
from celery import shared_task
from .service import process_attendee_search, generate_embeddings_for_photo
from photos.models import Photo

@shared_task
def task_generate_embeddings(photo_id):
    """Background task to process a new photo upload."""
    try:
        photo = Photo.objects.get(id=photo_id)
        generate_embeddings_for_photo(photo)
        return f"Success: Embeddings for Photo {photo_id}"
    except Photo.DoesNotExist:
        return "Error: Photo not found"

@shared_task
def task_run_attendee_scan(user_id, temp_selfie_path):
    """Background task to match a user selfie against event gallery."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        match_count = process_attendee_search(user, temp_selfie_path)
        return {"user_id": user_id, "match_count": match_count}
    finally:
        # Cleanup temp file after background processing
        if os.path.exists(temp_selfie_path):
            os.remove(temp_selfie_path)


# import os
# import logging
# from celery import shared_task
# from django.conf import settings
# from .models import Photo
# from accounts.models import User
# from tickets.models import Ticket

# logger = logging.getLogger(__name__)

# @shared_task
# def process_photo_ai(photo_id):
#     """
#     Background task to process a photo using DeepFace facial recognition.
#     Matches the photo against the reference images of all event attendees.
#     """
#     try:
#         photo = Photo.objects.get(id=photo_id)
#         event = photo.event
        
#         # 1. Get all attendees for this event who have a reference image
#         # Attendees are linked to events via Tickets
#         tickets = Ticket.objects.filter(event=event)
#         attendee_ids = [t.user.id for t in tickets if t.user.reference_image]
#         attendees = User.objects.filter(id__in=attendee_ids)
        
#         if not attendees.exists():
#             logger.info(f"No attendees with reference images for event {event.id}")
#             return f"No attendees to match for photo {photo_id}"

#         # 2. Perform Facial Recognition
#         # We try to import DeepFace here to avoid crashing the worker if it's not installed
#         try:
#             from deepface import DeepFace
#             import tempfile
            
#             # Temporary files for processing
#             with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as photo_tmp:
#                 photo_tmp.write(photo.image.read())
#                 photo_tmp.flush()
                
#                 matched_users = []
#                 for attendee in attendees:
#                     try:
#                         # Compare the photo with the attendee's reference image
#                         # Using VGG-Face or Facenet which are robust
#                         result = DeepFace.verify(
#                             img1_path=photo_tmp.name,
#                             img2_path=attendee.reference_image.path,
#                             enforce_detection=False,
#                             model_name="VGG-Face"
#                         )
                        
#                         if result.get("verified"):
#                             matched_users.append(attendee)
#                             logger.info(f"MATCH FOUND: Photo {photo_id} matched User {attendee.id}")
#                     except Exception as e:
#                         logger.error(f"Error matching Photo {photo_id} with User {attendee.id}: {e}")
                
#                 # 3. Update the photo's detected users
#                 if matched_users:
#                     photo.detected_users.add(*matched_users)
#                     return f"Successfully processed photo {photo_id}. Matched {len(matched_users)} users."
#                 else:
#                     return f"Processed photo {photo_id}. No matches found."

#         except ImportError:
#             logger.warning("DeepFace not installed. Skipping actual AI matching.")
#             # For demonstration/development, we could implement a simpler logic or leave as is
#             return "DeepFace library missing. AI processing skipped."

#     except Photo.DoesNotExist:
#         logger.error(f"Photo {photo_id} not found.")
#         return f"Error: Photo {photo_id} not found."
#     except Exception as e:
#         logger.error(f"Critical error in process_photo_ai: {e}")
#         return f"Error: {str(e)}"
