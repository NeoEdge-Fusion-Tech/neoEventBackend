import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from vendors.models import VendorBusiness

vb = VendorBusiness.objects.get(user__email="p@media.com")
print("Current business name:", vb.business_name)
vb.business_name = "P Media"
vb.save()
print("Updated business name:", vb.business_name)
