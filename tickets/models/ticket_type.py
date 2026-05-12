# tickets/models/ticket_type.py
from django.db import models
from django.conf import settings
import uuid
from core.models import UUIDPkField


class TicketType(UUIDPkField):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField()
    sold_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)


    # class Meta:
    #     constraints = [
    #         models.CheckConstraint(
    #             check=models.Q(sold_count__lte=models.F("quantity")),
    #             name="sold_count_lte_quantity"
    #         )
    #     ]
    
    @property
    def remaining(self):
        remaining = self.quantity - self.sold_count
        return max(remaining, 0)
    