import json
import logging
import boto3
from django.conf import settings

logger = logging.getLogger(__name__)

def dispatch_task(task_name: str, payload: dict):
    """
    Universal task dispatcher.
    If USE_SQS is True, pushes the task and payload to Amazon SQS.
    If False, imports and runs the Celery task locally using `.delay()`.
    """
    if getattr(settings, 'USE_SQS', False):
        try:
            sqs_client = boto3.client(
                'sqs',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
            
            queue_url = settings.AWS_SQS_QUEUE_URL
            message_body = json.dumps({
                "task": task_name,
                "payload": payload
            })
            
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body
            )
            
            logger.info(f"Successfully dispatched task {task_name} to SQS. MsgId: {response.get('MessageId')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to dispatch task {task_name} to SQS: {e}", exc_info=True)
            return False
            
    else:
        # Fallback to Celery for Local Development
        logger.info(f"USE_SQS is False. Dispatching {task_name} to local Celery worker.")
        
        if task_name == "notify_users_of_mapped_gallery":
            from photos.tasks import notify_users_of_mapped_gallery
            event_id = payload.get("event_id")
            notify_users_of_mapped_gallery.delay(event_id)
            return True
            
        elif task_name == "extract_faces_from_photos":
            from photos.tasks import extract_faces_from_photos
            photo_ids = payload.get("photo_ids")
            extract_faces_from_photos.delay(photo_ids)
            return True
            
        else:
            logger.error(f"Unknown Celery task: {task_name}")
            return False
