from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'registration', 'amount', 'gateway_name', 'status', 'created_at')
    list_filter = ('status', 'gateway_name', 'created_at')
    search_fields = ('reference', 'registration__registration_code', 'registration__attendee__user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
