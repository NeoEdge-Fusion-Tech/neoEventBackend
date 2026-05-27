# views/auth.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.conf import settings
from ..serializers.auth import (
    MyTokenObtainPairSerializer,
    TokenRefreshResponseSerializer,
    VendorRegisterSerializer,
    UserSerializer,
    # RegisterSerializer,
    EventOwnerRegisterSerializer,
    AttendeeRegistrationSerializer,
    AttendeeRegisterSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()



# from ..models import User


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
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data["access"]
        refresh_token = serializer.validated_data["refresh"]

        response = Response(
            {
                "access": access_token,
                "user": serializer.validated_data["user"],
            }
        )

        response.set_cookie(
            key=settings.AUTH_COOKIE,
            value=refresh_token,
            max_age=7 * 24 * 60 * 60,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
            path=settings.AUTH_COOKIE_PATH,
        )

        return response



@extend_schema(
    tags=["Authentication"],
    summary="Refresh Access Token",
    description="Refreshes the access token using the refresh token stored in cookies.",
    responses={
        200: TokenRefreshResponseSerializer,
        401: OpenApiResponse(description="Invalid or expired refresh token"),
    }
)
class RefreshTokenView(APIView):
    authentication_classes = ()
    permission_classes = [AllowAny]
    throttle_scope = "login"
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE)

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)

            user_id = refresh["user_id"]

            user = User.objects.get(id=user_id)

            data = {
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }

            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS"):

                refresh.blacklist()

                new_refresh = RefreshToken.for_user(user)

                response = Response(data)

                response.set_cookie(
                    key=settings.AUTH_COOKIE,
                    value=str(new_refresh),
                    max_age=7 * 24 * 60 * 60,
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,
                    path=settings.AUTH_COOKIE_PATH,
                )

                return response

            return Response(data)

        except (TokenError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Logout User",
    description="Blacklist the refresh token and clear auth cookie.",
    responses={
        200: OpenApiResponse(
            response={"message": "Logged out successfully."},
            description="Logout successful"
        ),
    }
)
class LogoutView(APIView):
    authentication_classes = ()
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie(
            settings.AUTH_COOKIE,
            path=settings.AUTH_COOKIE_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

        return response


@extend_schema(
    tags=["Authentication"],
    summary="Register Event Owner",
    request=EventOwnerRegisterSerializer,
    responses={201: OpenApiResponse(description="Owner account created successfully.")},
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
    serializer_class = EventOwnerRegisterSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [AllowAny]
    

@extend_schema(
    tags=["Authentication"],
    summary="Register Vendor",
    request=VendorRegisterSerializer,
    responses={201: OpenApiResponse(description="Vendor account created successfully.")},
    examples=[
        OpenApiExample(
            "Vendor Registration Example",
            value={
                "username": "lensmaster",
                "email": "photographer@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "phone_number": "+2348012345678",
                "vendor_subtype": "PHOTOGRAPHER",
            },
            request_only=True,
        ),
    ],
)
class VendorRegisterView(generics.CreateAPIView):
    serializer_class = VendorRegisterSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save() 

        # Now we just wrap that user in a nice response
        return Response(
            {
                "message": "Vendor account created successfully.",
                "user_id": user.id,
                # "onboarding_status": user.onboarding_status,
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=["Attendees"],
    summary="Register Event Attendee Account",
    description=(
        "Expressly registers an attendee for a platform User account."
    ),
    request=AttendeeRegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="Attendee account created successfully."
        ),
        400: OpenApiResponse(
            description="Validation error."
        ),
    },
    examples=[
        OpenApiExample(
            "Attendee Account Signup Example",
            value={
                "username": "janedoe",
                "email": "jane@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone_number": "+2348011111111",
            },
            request_only=True,
        ),
    ],
)
class AttendeeRegistrationView(generics.CreateAPIView):

    serializer_class = AttendeeRegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [UserRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        attendee = getattr(user, "attendee_profile", None)
        return Response(
            {
                "message": "Attendee account created successfully.",
                "user_id": user.id,
                "registration_code": attendee.registration_code if attendee else None,
                "attendee_id": attendee.id if attendee else None,
            },
            status=status.HTTP_201_CREATED,
        )
    
