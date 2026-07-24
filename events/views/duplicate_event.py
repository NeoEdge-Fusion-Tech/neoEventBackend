import uuid
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema

from ..models import Event
from ..permissions import IsEventOwnerRole
from tickets.models import TicketType
from events.models import CustomQuestion

class DuplicateEventView(APIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]

    @extend_schema(
        tags=["Event Management"],
        summary="Duplicate an existing event",
        description="Creates a copy of an existing event including its ticket types and custom questions. Does not copy attendees or vendors."
    )
    def post(self, request, event_id, *args, **kwargs):
        original_event = get_object_or_404(Event, id=event_id)
        self.check_object_permissions(self.request, original_event)

        # 1. Duplicate Event
        new_event = Event.objects.get(id=original_event.id)
        new_event.id = uuid.uuid4()
        new_event.title = f"Copy of {original_event.title}"
        new_event.slug = f"{slugify(new_event.title)}-{str(new_event.id)[:8]}"
        new_event.status = Event.Status.DRAFT
        new_event.is_public = False
        new_event.save()

        # 2. Duplicate Ticket Types
        for ticket in original_event.ticket_types.all():
            ticket.id = uuid.uuid4()
            ticket.event = new_event
            ticket.save()

        # 3. Duplicate Custom Questions
        for question in original_event.custom_questions.all():
            question.id = uuid.uuid4()
            question.event = new_event
            question.save()

        return Response({"id": new_event.id, "slug": new_event.slug}, status=status.HTTP_201_CREATED)
