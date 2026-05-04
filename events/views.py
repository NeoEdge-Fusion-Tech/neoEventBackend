from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateSerializer,
)

from .permissions import IsEventOwner


class EventListView(generics.ListAPIView):

    serializer_class = EventListSerializer
    permission_classes = [AllowAny]

    queryset = Event.objects.filter(
        is_public=True
    ).select_related("owner")

class EventDetailView(generics.RetrieveAPIView):

    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]

    queryset = Event.objects.select_related(
        "owner"
    )

    lookup_field = "slug"

class EventCreateView(generics.CreateAPIView):

    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated]

class EventUpdateView(generics.UpdateAPIView):

    serializer_class = EventCreateSerializer

    permission_classes = [
        IsAuthenticated,
        IsEventOwner,
    ]

    queryset = Event.objects.all()

    lookup_field = "id"

class EventUpdateView(generics.UpdateAPIView):

    serializer_class = EventCreateSerializer

    permission_classes = [
        IsAuthenticated,
        IsEventOwner,
    ]

    queryset = Event.objects.all()

    lookup_field = "id"


# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from .models import Event, EventPhotographer
# from .serializers import EventSerializer, EventPhotographerSerializer
# from django.shortcuts import get_object_or_404

# class EventListCreateView(generics.ListCreateAPIView):
#     serializer_class = EventSerializer

#     def get_queryset(self):
#         queryset = Event.objects.all()
#         active_only = self.request.query_params.get('active_only', None)
#         if active_only == 'true':
#             # This filters by the 'status' field.
#             return queryset.filter(status='ACTIVE')
#         return queryset

#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return [permissions.IsAuthenticated()]
#         return [permissions.AllowAny()]

#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)

# class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Event.objects.all()
#     serializer_class = EventSerializer

#     def get_permissions(self):
#         if self.request.method in ['PUT', 'PATCH', 'DELETE']:
#             return [permissions.IsAuthenticated()] # Should ideally check for ownership
#         return [permissions.AllowAny()]

#     def perform_update(self, serializer):
#         if self.get_object().owner != self.request.user:
#             return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
#         serializer.save()

# class AssignedEventListView(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = EventSerializer

#     def get_queryset(self):
#         queryset = Event.objects.filter(event_photographers__photographer=self.request.user)
#         pending_only = self.request.query_params.get('pending_only', None)
        
#         if pending_only == 'true':
#             # Filter events where the photographer has NOT uploaded any photos yet
#             from photos.models import Photo
#             events_with_photos = Photo.objects.filter(uploader=self.request.user).values_list('event_id', flat=True)
#             queryset = queryset.exclude(id__in=events_with_photos)
            
#         return queryset

# class OwnedEventListView(generics.ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = EventSerializer

#     def get_queryset(self):
#         return Event.objects.filter(owner=self.request.user)

# class EventPhotographerCreateView(generics.CreateAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = EventPhotographerSerializer

#     def perform_create(self, serializer):
#         # Implementation could send email invite here
#         serializer.save()

# class PhotographerEventDetailView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def get(self, request, unique_code):
#         link = get_object_or_404(EventPhotographer, unique_code=unique_code)
#         serializer = EventSerializer(link.event)
#         return Response({
#             "event": serializer.data,
#             "photographer_link": EventPhotographerSerializer(link).data
#         })
