# tickets/views/checkin.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..models.event_registration import EventRegistration
from ..serializers.checkin import EventCheckInSerializer


class EventCheckInView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, registration_code):
        registration = get_object_or_404(
            EventRegistration.objects.select_related(
                "event",
                "attendee",
            ),
            registration_code=registration_code,
        )

        # ------------------------------------------
        # Prevent duplicate check-in today
        # ------------------------------------------
        from django.utils import timezone
        from ..models import DailyCheckIn
        target_date_str = request.data.get("date")
        if target_date_str:
            from datetime import datetime
            try:
                today = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.now().date()

        if DailyCheckIn.objects.filter(registration=registration, date=today).exists():
            return Response(
                {
                    "detail": f"Attendee already checked in for {today}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        device_id = request.data.get("device_id")
        DailyCheckIn.objects.create(
            registration=registration,
            device_id=device_id,
            date=today
        )

        # ------------------------------------------
        # Mark checked in globally for first time
        # ------------------------------------------
        if not registration.checked_in:
            registration.checked_in = True
            registration.status = EventRegistration.Status.CHECKED_IN
            registration.save(update_fields=["checked_in", "status"])

        serializer = EventCheckInSerializer(registration)

        return Response(
            {
                "message": "Check-in successful.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    