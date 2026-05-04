# views/auth.py

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers.auth import (
    MyTokenObtainPairSerializer,
    VendorRegisterSerializer,
    RegisterSerializer,
    AttendeeRegistrationSerializer,
)

from ..models import User


@extend_schema(
    tags=["Authentication"],
    summary="Login User",
    description=(
        "Authenticate an event owner or vendor and "
        "return JWT access and refresh tokens."
    ),
    request=MyTokenObtainPairSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful."
        ),
        401: OpenApiResponse(
            description="Invalid credentials."
        ),
    },
)
class LoginView(TokenObtainPairView):

    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
    summary="Register Event Owner",
    description=(
        "Creates a new event owner account."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="Event owner account created successfully."
        ),
        400: OpenApiResponse(
            description="Validation error."
        ),
    },
    examples=[
        OpenApiExample(
            "Owner Registration Example",
            value={
                "username": "eventmaster",
                "email": "owner@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
            },
            request_only=True,
        ),
    ],
)
class EventOwnerRegisterView(generics.CreateAPIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        data = request.data.copy()
        data["role"] = User.Role.OWNER

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Event owner account created successfully.",
                "user_id": user.id,
                "username": user.username,
                "role": user.role,
                "onboarding_status": user.onboarding_status,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Register Vendor",
    description=(
        "Creates a new vendor account for photographers, "
        "videographers, or planners."
    ),
    request=VendorRegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="Vendor account created successfully."
        ),
        400: OpenApiResponse(
            description="Validation error."
        ),
    },
    examples=[
        OpenApiExample(
            "Vendor Registration Example",
            value={
                "username": "lensmaster",
                "email": "photographer@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+2348012345678",
                "vendor_subtype": "PHOTOGRAPHER",
                "service_title": "Wedding Photographer",
                "service_areas": "Lagos, Abuja",
            },
            request_only=True,
        ),
    ],
)
class VendorRegisterView(generics.CreateAPIView):

    serializer_class = VendorRegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Attendees"],
    summary="Register Event Attendee",
    description=(
        "Registers an attendee for event participation "
        "without requiring platform authentication."
    ),
    request=AttendeeRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            description="Attendee registered successfully."
        ),
        400: OpenApiResponse(
            description="Validation error."
        ),
    },
    examples=[
        OpenApiExample(
            "Attendee Registration Example",
            value={
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone_number": "+2348011111111",
            },
            request_only=True,
        ),
    ],
)
class AttendeeRegistrationView(generics.CreateAPIView):

    serializer_class = AttendeeRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendee = serializer.save()

        return Response(
            {
                "message": "Registration successful.",
                "registration_code": attendee.registration_code,
                "attendee_id": attendee.id,
            },
            status=status.HTTP_201_CREATED,
        )
    
