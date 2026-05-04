import uuid
import RandomUUID
from django.db import models
# class UUIDPrimaryKeyField(models.UUIDField):
#     def __init__(self, *args, **kwargs):
#         kwargs["primary_key"] = True
#         kwargs.setdefault("db_default", RandomUUID())


# Custom field class for UUID primary keys
class UUIDPrimaryKeyField(models.UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("primary_key", True)
        kwargs.setdefault("default", uuid.uuid4)
        kwargs.setdefault("editable", False)
        super().__init__(*args, **kwargs)

