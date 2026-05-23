from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Event
from accounts.models.validator_profile import ValidatorProfile

User = get_user_model()

class ValidatorLoginView(APIView):
    """
    Login endpoint specifically for Validators.
    Expects username and password. Returns tokens and user details.
    """
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = User.objects.filter(username=username).first()
        if not user or not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_validator:
            return Response({"detail": "User is not a validator."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        
        # Ensure profile exists
        profile, _ = ValidatorProfile.objects.get_or_create(user=user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "validator": {
                "id": user.id,
                "username": user.username,
                "device_name": profile.device_name,
                "is_active": profile.is_active
            }
        })

class ValidatorOnboardingView(APIView):
    """
    Onboarding endpoint to set device name and status for a validator.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_validator:
            return Response({"detail": "Only validators can onboard."}, status=status.HTTP_403_FORBIDDEN)

        device_name = request.data.get("device_name")
        is_active = request.data.get("is_active", True)

        profile, _ = ValidatorProfile.objects.get_or_create(user=user)
        if device_name:
            profile.device_name = device_name
        
        # Depending on security, maybe they can't set their own active status if it requires admin approval.
        # Assuming for now they can toggle it to active during onboarding.
        profile.is_active = is_active
        profile.save()

        return Response({
            "message": "Validator onboarding complete.",
            "device_name": profile.device_name,
            "is_active": profile.is_active
        })

class ValidatorEventListView(APIView):
    """
    List events. A validator might be assigned to specific events,
    but for now we return public or active events they can select.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_validator:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        events = Event.objects.filter(status="ACTIVE")
        
        data = []
        for e in events:
            data.append({
                "id": str(e.id),
                "title": e.title,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "venue_name": e.venue_name,
                "banner_image": e.banner_image.url if e.banner_image else None
            })
            
        return Response(data)
