import os
import json
import logging
import django

# Setup Django ORM outside the handler to take advantage of Lambda execution environment reuse
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.tasks import notify_users_of_mapped_gallery, extract_faces_from_photos

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    AWS Lambda entry point for SQS trigger.
    Processes SQS Records and executes the corresponding Django background task.
    """
    logger.info(f"Received SQS Event with {len(event.get('Records', []))} records.")
    
    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            task_name = body.get('task')
            payload = body.get('payload', {})
            
            logger.info(f"Processing SQS task: {task_name}")
            
            if task_name == "notify_users_of_mapped_gallery":
                event_id = payload.get("event_id")
                if not event_id:
                    logger.error("Missing event_id in payload")
                    continue
                    
                # Execute synchronously inside the Lambda container
                result = notify_users_of_mapped_gallery(event_id)
                logger.info(f"Task completed successfully: {result}")
                
            elif task_name == "extract_faces_from_photos":
                photo_ids = payload.get("photo_ids")
                if not photo_ids:
                    logger.error("Missing photo_ids in payload")
                    continue
                
                result = extract_faces_from_photos(photo_ids)
                logger.info(f"Face extraction queued/completed successfully.")
                
            else:
                logger.warning(f"Unknown task name received: {task_name}")
                
        except Exception as e:
            logger.error(f"Error processing SQS record: {str(e)}", exc_info=True)
            # Depending on error handling, you might want to raise the exception 
            # so AWS SQS moves it to a Dead Letter Queue (DLQ).
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed SQS records.")
    }
