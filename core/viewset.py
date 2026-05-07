from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'message': 'Welcome to the API',
        # 'documentation': 'https://api-docs.example.com',
        'domentation': request.build_absolute_uri('/api/schema'),
        'status': 'up',

        'admin': request.build_absolute_uri('/admin/'),

        'login': reverse('accounts:login', request=request, format=format),
        'vendor_registration': reverse('accounts:vendor-register', request=request, format=format),
        'owner_registration': reverse('accounts:owner-register', request=request, format=format),
        'attendee_registration': reverse('accounts:attendee-register', request=request, format=format),
        'events': reverse('event-list', request=request, format=format),
        # 'tickets': reverse('ticket-list', request=request, format=format),
    })


class BaseViewSet(ModelViewSet):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.archive()
        return Response(status=status.HTTP_204_NO_CONTENT)

