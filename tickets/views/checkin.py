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
        # Prevent duplicate check-in
        # ------------------------------------------

        if registration.checked_in:

            return Response(
                {
                    "detail": "Attendee already checked in."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------
        # Mark checked in
        # ------------------------------------------

        registration.checked_in = True

        registration.status = (
            EventRegistration.Status.CHECKED_IN
        )

        registration.save(
            update_fields=[
                "checked_in",
                "status",
            ]
        )

        serializer = EventCheckInSerializer(registration)

        return Response(
            {
                "message": "Check-in successful.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    