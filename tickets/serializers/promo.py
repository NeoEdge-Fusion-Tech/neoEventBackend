from rest_framework import serializers
from ..models.promo_code import PromoCode

class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = PromoCode
        fields = (
            "id", "code", "valid_from", "valid_until", "max_uses", "current_uses",
            "discount_percentage", "discount_amount", "is_active", "is_valid"
        )
        read_only_fields = ("id", "current_uses", "is_valid")
