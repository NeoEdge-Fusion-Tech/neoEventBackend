from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from events.permissions import IsEventOwnerRole
from ..models.promo_code import PromoCode
from ..serializers.promo import PromoCodeSerializer
from django.shortcuts import get_object_or_404
from events.models import Event

@extend_schema(tags=["Promo Codes"])
class PromoCodeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    serializer_class = PromoCodeSerializer

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        return PromoCode.objects.filter(event_id=event_id, event__owner=self.request.user)

    def perform_create(self, serializer):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, id=event_id, owner=self.request.user)
        serializer.save(event=event)

@extend_schema(tags=["Promo Codes"])
class PromoCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    serializer_class = PromoCodeSerializer
    lookup_field = "id"

    def get_queryset(self):
        return PromoCode.objects.filter(event__owner=self.request.user)
