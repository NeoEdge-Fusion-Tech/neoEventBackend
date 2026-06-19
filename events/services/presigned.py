import time
import uuid
from django.conf import settings


def _resource_type_for(file_type: str) -> str:
    if file_type and file_type.startswith("video/"):
        return "video"
    return "image"


def generate_event_setup_presigned_urls(files: list, base_url: str = "http://localhost:8000") -> list:
    """
    Generates direct-upload instructions for event assets, so large files
    (banner videos especially) never pass through our own API — avoiding
    serverless request-body size limits. Each response item carries a
    "provider" telling the frontend which upload strategy to use.
    """
    use_s3 = getattr(settings, "USE_S3", True)
    use_cloudinary = getattr(settings, "USE_CLOUDINARY", False)

    if use_s3:
        return _generate_s3_presigned_urls(files)
    if use_cloudinary:
        return _generate_cloudinary_signed_uploads(files)
    return _generate_local_proxy_urls(files, base_url)


def _generate_local_proxy_urls(files: list, base_url: str) -> list:
    responses = []
    for file_obj in files:
        file_name = file_obj.get("file_name")
        unique_file_name = f"{uuid.uuid4()}_{file_name}"
        object_key = f"event_banners/{unique_file_name}"

        responses.append({
            "provider": "local",
            "original_name": file_name,
            "object_key": object_key,
            # React frontend PUTs the raw file to this proxy URL
            "presigned_url": f"{base_url}/api/photos/local-upload/{object_key}",
            # Best-effort prediction; the upload response's own "url" is authoritative
            "full_url": f"{base_url}{settings.MEDIA_URL}{object_key}",
        })
    return responses


def _generate_s3_presigned_urls(files: list) -> list:
    import boto3

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=boto3.session.Config(signature_version="s3v4"),
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME

    responses = []
    for file_obj in files:
        file_name = file_obj.get("file_name")
        file_type = file_obj.get("file_type")

        unique_file_name = f"{uuid.uuid4()}_{file_name}"
        object_key = f"event_banners/{unique_file_name}"

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket_name, "Key": object_key, "ContentType": file_type},
            ExpiresIn=3600,
        )

        responses.append({
            "provider": "s3",
            "original_name": file_name,
            "object_key": object_key,
            "presigned_url": presigned_url,
            "full_url": f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_key}",
        })
    return responses


def _generate_cloudinary_signed_uploads(files: list) -> list:
    import cloudinary
    import cloudinary.utils

    cloud_name = settings.CLOUDINARY_CLOUD_NAME
    api_key = settings.CLOUDINARY_API_KEY
    api_secret = settings.CLOUDINARY_API_SECRET

    responses = []
    for file_obj in files:
        file_name = file_obj.get("file_name")
        file_type = file_obj.get("file_type")
        resource_type = _resource_type_for(file_type)

        unique_file_name = f"{uuid.uuid4()}_{file_name}"
        object_key = f"event_banners/{unique_file_name}"
        # Cloudinary appends the format extension itself; the public_id should omit it.
        public_id = object_key.rsplit(".", 1)[0] if "." in object_key.split("/")[-1] else object_key

        timestamp = int(time.time())
        params_to_sign = {"timestamp": timestamp, "public_id": public_id}
        signature = cloudinary.utils.api_sign_request(params_to_sign, api_secret)

        responses.append({
            "provider": "cloudinary",
            "original_name": file_name,
            "object_key": object_key,
            "presigned_url": f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload",
            "fields": {
                "api_key": api_key,
                "timestamp": timestamp,
                "signature": signature,
                "public_id": public_id,
            },
        })
    return responses
