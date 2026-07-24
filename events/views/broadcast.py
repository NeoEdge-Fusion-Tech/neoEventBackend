from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from ..models import Event, BroadcastMessage
from ..serializers.broadcast import BroadcastMessageSerializer
from tickets.models import EventRegistration

class BroadcastMessageCreateView(generics.CreateAPIView):
    serializer_class = BroadcastMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        event_id = self.kwargs.get('id')
        event = get_object_or_404(Event, id=event_id)
        
        if event.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to broadcast for this event.")
            
        broadcast = serializer.save(event=event)
        
        # Fetch recipients
        registrations = EventRegistration.objects.filter(event=event)
        if broadcast.recipient_type == BroadcastMessage.RecipientType.CONFIRMED:
            registrations = registrations.filter(status=EventRegistration.Status.CONFIRMED)
        elif broadcast.recipient_type == BroadcastMessage.RecipientType.CHECKED_IN:
            registrations = registrations.filter(checked_in=True)
            
        emails = list(set([reg.attendee_email for reg in registrations if reg.attendee_email]))
        phones = list(set([reg.attendee_phone for reg in registrations if reg.attendee_phone]))

        import logging
        logger = logging.getLogger(__name__)
        
        # Send notifications
        success_count = 0
        if broadcast.channel == BroadcastMessage.ChannelChoices.EMAIL:
            if emails:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@neoevents.com')
                msg = EmailMultiAlternatives(
                    subject=broadcast.subject,
                    body=broadcast.message,
                    from_email=from_email,
                    bcc=emails
                )
                try:
                    msg.send(fail_silently=True)
                    success_count = len(emails)
                except Exception as e:
                    logger.error(f"Failed to send broadcast email: {e}")
        elif broadcast.channel == BroadcastMessage.ChannelChoices.SMS:
            # Mocking SMS Dispatch
            if phones:
                for phone in phones:
                    logger.info(f"Mock SMS sent to {phone}: {broadcast.message}")
                success_count = len(phones)
        elif broadcast.channel == BroadcastMessage.ChannelChoices.WHATSAPP:
            # Mocking WHATSAPP Dispatch
            if phones:
                for phone in phones:
                    logger.info(f"Mock WhatsApp sent to {phone}: {broadcast.message}")
                success_count = len(phones)

        if success_count > 0:
            broadcast.sent_count = success_count
            broadcast.save(update_fields=['sent_count'])

class BroadcastMessageListView(generics.ListAPIView):
    serializer_class = BroadcastMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        event_id = self.kwargs.get('id')
        event = get_object_or_404(Event, id=event_id)
        if event.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view broadcasts for this event.")
        return BroadcastMessage.objects.filter(event=event)
