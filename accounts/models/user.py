# models/user.py 
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from core.models import UUIDPkField


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("onboarding_status", "ACTIVE")
        extra_fields.setdefault("is_email_verified", True)
        
        if extra_fields.get("role") != "ADMIN":
            raise ValueError("Superuser must have role='ADMIN'.")

        return super().create_superuser(username, email, password, **extra_fields)


class User(UUIDPkField, AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        OWNER = "OWNER", "Event Owner"
        VENDOR = "VENDOR", "Vendor"
        ATTENDEE = "ATTENDEE", "Attendee"
        VALIDATOR = "VALIDATOR", "Validator"

    class AdminSubtype(models.TextChoices):
        OPS = "OPS", "Operations"
        CUSTOMER = "CUSTOMER", "Customer Support"

    class OnboardingStatus(models.TextChoices):
        PENDING_EMAIL = "PENDING_EMAIL", "Pending Email Verification"
        PROFILE_INCOMPLETE = "PROFILE_INCOMPLETE", "Profile Incomplete"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        default=Role.ATTENDEE,
        choices=Role.choices,
        db_index=True,
    )

    # New field for Admin differentiation
    admin_subtype = models.CharField(
        max_length=20,
        choices=AdminSubtype.choices,
        null=True, # Nullable because not all users are Admins
        blank=True,
    )

    onboarding_status = models.CharField(
        max_length=30,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING_EMAIL,
    )

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    
    # OTP Fields for Email Verification
    email_verification_otp = models.CharField(max_length=6, null=True, blank=True)
    email_verification_otp_created_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-date_joined"]

    @property
    def is_admin_user(self):
        """Helper for your permission classes"""
        return self.role == self.Role.ADMIN

    @property
    def is_ops_admin(self):
        return self.is_admin_user and self.admin_subtype == self.AdminSubtype.OPS

    @property
    def is_customer_admin(self):
        return self.is_admin_user and self.admin_subtype == self.AdminSubtype.CUSTOMER
    
    @property
    def is_vendor(self):
        return self.role == self.Role.VENDOR

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_validator(self):
        return self.role == self.Role.VALIDATOR

    def __str__(self):
        return f"{self.username} ({self.role})"
    