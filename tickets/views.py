# # tickets/views.py

from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import (
    TicketType,
    EventRegistration,
)

from .serializers import (
    TicketTypeSerializer,
    EventRegistrationSerializer,
)

class EventTicketTypeListView(generics.ListAPIView):

    serializer_class = TicketTypeSerializer

    permission_classes = [AllowAny]

    def get_queryset(self):

        return TicketType.objects.filter(
            event_id=self.kwargs["event_id"],
            is_active=True,
        )


class EventRegistrationCreateView(generics.CreateAPIView):

    serializer_class = EventRegistrationSerializer

    permission_classes = [AllowAny]


class RegistrationDetailView(generics.RetrieveAPIView):

    serializer_class = EventRegistrationSerializer

    permission_classes = [AllowAny]

    queryset = EventRegistration.objects.select_related(
        "event",
        "attendee",
        "ticket_type",
    )

    lookup_field = "registration_code"

    
# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from .models import Registration, Ticket
# from .serializers import RegistrationSerializer, TicketSerializer

# class RegistrationListCreateView(generics.ListCreateAPIView):
#     serializer_class = RegistrationSerializer
#     permission_classes = (permissions.IsAuthenticated,)

#     def get_queryset(self):
#         return Registration.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         registration = serializer.save(user=self.request.user)
#         # Create a ticket automatically on registration
#         Ticket.objects.create(registration=registration)

# class TicketDetailView(generics.RetrieveAPIView):
#     queryset = Ticket.objects.all()
#     serializer_class = TicketSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     lookup_field = 'registration__id' # Allow looking up by registration ID
#     lookup_url_kwarg = 'reg_id'

