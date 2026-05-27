from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count
from events.models.vendor import EventVendor
from accounts.models import VendorProfile

class VendorTypesView(APIView):
    """
    Returns a unique list of all vendor roles/subtypes currently in the system,
    combined with the defaults.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        # Base defaults
        types_set = {
            "PHOTOGRAPHER", "VIDEOGRAPHER", "PLANNER", "CATERER", "DECORATOR"
        }
        
        # Get from EventVendor
        event_roles = EventVendor.objects.values_list('role', flat=True).distinct()
        for r in event_roles:
            if r:
                types_set.add(r.upper())
                
        # Get from VendorProfile
        profile_roles = VendorProfile.objects.values_list('subtype', flat=True).distinct()
        for pr in profile_roles:
            if pr:
                types_set.add(pr.upper())
                
        # Return sorted list
        return Response(sorted(list(types_set)))
