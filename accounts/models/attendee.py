# models/attendee.py
import uuid
from django.db import models
from django.conf import settings

class AttendeeProfile(models.Model):
    # Nullable so they can register for an event WITHOUT a User account initially
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendee_profile",
        null=True,
        blank=True
    )
    
    # Data captured at registration
    full_name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True) 
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Security/Access
    registration_code = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    reference_image = models.ImageField(
        upload_to="attendee_references/", 
        null=True, 
        blank=True,
        help_text="For facial recognition entry."
    )

    def __str__(self):
        return f"Attendee: {self.full_name} ({self.email})"
    

# import uuid
# from django.db import models
# from django.conf import settings

# class AttendeeProfile(models.Model):
#     # Nullable for guests who haven't created an account yet
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL, # Don't delete the attendee data if user is deleted
#         related_name="attendee_profile",
#         null=True,
#         blank=True
#     )
    
#     # If user is None, use these. If user exists, these should stay synced or be ignored.
#     full_name = models.CharField(max_length=255)
#     guest_email = models.EmailField(db_index=True, null=True, blank=True) 
    
#     registration_code = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
#     reference_image = models.ImageField(
#         upload_to="attendee_references/", 
#         null=True, 
#         blank=True,
#         help_text="Used for facial recognition entry."
#     )

#     @property
#     def email(self):
#         return self.user.email if self.user else self.guest_email

#     def __str__(self):
#         return f"Attendee: {self.full_name}"