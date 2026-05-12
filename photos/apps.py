from django.apps import AppConfig


class PhotosConfig(AppConfig):
    name = 'photos'

    def ready(self):
        import photos.signals
