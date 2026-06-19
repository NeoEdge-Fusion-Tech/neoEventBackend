"""
Storage backends that pass already-resolved external URLs straight through.

Direct-to-Cloudinary/S3 uploads (used to bypass the serverless function's
request-body size limit) hand the frontend a final, authoritative URL
(e.g. Cloudinary's `secure_url`). When that URL is later stored on a model's
FileField/ImageField, Django's default `.url` behavior re-derives a URL from
the stored name via the storage backend — which can disagree with the URL
the file actually lives at (wrong resource type, missing version, wrong
bucket path, etc). These wrappers make `.url` a no-op passthrough whenever
the stored name is already an absolute URL.
"""


def _is_absolute_url(name):
    return bool(name) and (name.startswith("http://") or name.startswith("https://"))


try:
    from cloudinary_storage.storage import MediaCloudinaryStorage

    class PassthroughCloudinaryStorage(MediaCloudinaryStorage):
        def url(self, name):
            if _is_absolute_url(name):
                return name
            return super().url(name)
except ImportError:
    pass


try:
    from storages.backends.s3boto3 import S3Boto3Storage

    class PassthroughS3Storage(S3Boto3Storage):
        def url(self, name, *args, **kwargs):
            if _is_absolute_url(name):
                return name
            return super().url(name, *args, **kwargs)
except ImportError:
    pass
