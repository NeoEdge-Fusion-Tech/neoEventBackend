# tickets/views/export.py
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from events.models import Event
from events.permissions import IsEventOwnerRole
from ..models import EventRegistration, DailyCheckIn

class EventExportView(APIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, owner=request.user)
        export_type = request.query_params.get("type", "registrations")
        
        response = HttpResponse(content_type='text/csv')
        
        if export_type == "daily_checkins":
            response['Content-Disposition'] = f'attachment; filename="event_{event.id}_daily_checkins.csv"'
            writer = csv.writer(response)
            writer.writerow(['Registration Code', 'Name', 'Email', 'Ticket Type', 'Check-in Date', 'Check-in Time', 'Device ID'])
            
            checkins = DailyCheckIn.objects.filter(
                registration__event=event
            ).select_related('registration', 'registration__ticket_type', 'registration__attendee')
            
            for c in checkins:
                reg = c.registration
                name = reg.attendee_name or (reg.attendee.full_name if reg.attendee else "Unknown")
                email = reg.attendee_email or (reg.attendee.email if reg.attendee else "")
                ticket = reg.ticket_type.name if reg.ticket_type else "None"
                
                writer.writerow([
                    reg.registration_code,
                    name,
                    email,
                    ticket,
                    c.date,
                    c.time,
                    c.device_id or ""
                ])
                
        else:
            # Default to registrations
            response['Content-Disposition'] = f'attachment; filename="event_{event.id}_registrations.csv"'
            writer = csv.writer(response)
            writer.writerow(['Registration Code', 'Name', 'Email', 'Ticket Type', 'Group Name', 'Status', 'Checked In', 'Registered At', 'Total Days Attended'])
            
            status_filter = request.query_params.get("status")
            qs = EventRegistration.objects.filter(event=event).select_related('attendee', 'ticket_type')
            
            if status_filter == 'CHECKED_IN':
                qs = qs.filter(checked_in=True)
            elif status_filter == 'NOT_CHECKED_IN':
                qs = qs.filter(checked_in=False)
                
            for reg in qs:
                name = reg.attendee_name or (reg.attendee.full_name if reg.attendee else "Unknown")
                email = reg.attendee_email or (reg.attendee.email if reg.attendee else "")
                ticket = reg.ticket_type.name if reg.ticket_type else "None"
                days_attended = reg.daily_checkins.count()
                
                writer.writerow([
                    reg.registration_code,
                    name,
                    email,
                    ticket,
                    reg.group_name or "",
                    reg.status,
                    "Yes" if reg.checked_in else "No",
                    reg.registered_at,
                    days_attended
                ])
                
        return response
