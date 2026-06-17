import boto3
import uuid
from django.conf import settings

def generate_event_setup_presigned_urls(files: list, base_url: str = "http://localhost:8000") -> list:
    """
    Generates presigned upload URLs (or local proxy URLs) for event assets.
    """
    responses = []
    
    # We are in S3 production if DEBUG is False, TESTING is False, and AWS bucket is configured
    use_s3 = (
        not getattr(settings, 'DEBUG', True) 
        and not getattr(settings, 'TESTING', False)
        and getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') != ''
    )
    
    if not use_s3:
        # Local Development proxy (simulate S3 PUT)
        for file_obj in files:
            file_name = file_obj.get("file_name")
            unique_file_name = f"{uuid.uuid4()}_{file_name}"
            object_key = f"event_banners/{unique_file_name}"
            
            # React frontend will PUT the file to this proxy URL
            local_put_url = f"{base_url}/api/photos/local-upload/{object_key}"
            
            # The final URL served by Django
            full_url = f"{base_url}{settings.MEDIA_URL}{object_key}"
            
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
        object_key = f"event_banners/{unique_file_name}"
        
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
