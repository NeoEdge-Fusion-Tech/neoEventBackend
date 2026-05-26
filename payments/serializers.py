from rest_framework import serializers

class InitializePaymentSerializer(serializers.Serializer):
    registration_id = serializers.UUIDField(required=True)
    callback_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

class VerifyPaymentSerializer(serializers.Serializer):
    reference = serializers.CharField(required=True)
