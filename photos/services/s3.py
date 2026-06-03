import boto3
import uuid
from django.conf import settings

def generate_bulk_presigned_upload_urls(event_name: str, event_id: str, files: list) -> list:
    """
    Generates multiple pre-signed S3 URLs for bulk uploading.
    If USE_S3 is False (local dev), generates proxy URLs hitting a local Django endpoint.
    Returns a list of dicts containing the presigned URL, object key, and full public URL.
    """
    clean_event_name = "".join(c if c.isalnum() else "_" for c in event_name)
    responses = []
    
    if not getattr(settings, 'USE_S3', True):
        # Local Development Branch
        # Generate local upload proxy URLs
        for file_obj in files:
            file_name = file_obj.get("file_name")
            unique_file_name = f"{uuid.uuid4()}_{file_name}"
            object_key = f"events/{clean_event_name}_{event_id}/gallery/images/{unique_file_name}"
            
            # The URL the React frontend will PUT the file to
            # (Assuming the API runs on localhost:8000 in dev)
            local_put_url = f"http://localhost:8000/api/photos/local-upload/{object_key}"
            
            # The final URL it will be served from by Django's media server
            full_url = f"http://localhost:8000{settings.MEDIA_URL}{object_key}"
            
            responses.append({
                "presigned_url": local_put_url,
                "object_key": object_key,
                "full_url": full_url,
                "original_name": file_name
            })
        return responses

    # Production Branch (AWS S3)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=boto3.session.Config(signature_version='s3v4')
    )
    
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    
    for file_obj in files:
        file_name = file_obj.get("file_name")
        file_type = file_obj.get("file_type")
        
        unique_file_name = f"{uuid.uuid4()}_{file_name}"
        object_key = f"events/{clean_event_name}_{event_id}/gallery/images/{unique_file_name}"
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': file_type,
            },
            ExpiresIn=3600
        )
        
        # Calculate the final permanent public URL of the object
        full_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_key}"
        
        responses.append({
            "presigned_url": presigned_url,
            "object_key": object_key,
            "full_url": full_url,
            "original_name": file_name
        })
        
    return responses
