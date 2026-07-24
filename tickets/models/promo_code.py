# tickets/models/promo_code.py
from django.db import models
from core.models import UUIDPkField
from django.utils import timezone

class PromoCode(UUIDPkField):
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="promo_codes"
    )
    code = models.CharField(max_length=50, db_index=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    # Can use either percentage or absolute amount
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("event", "code")

    def __str__(self):
        return f"{self.code} - {self.event.title}"
        
    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True
