import uuid
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from tickets.models import EventRegistration
from .models import PaymentTransaction
from .serializers import InitializePaymentSerializer, VerifyPaymentSerializer
from .gateways.factory import get_payment_provider

@extend_schema(tags=["Payments"])
class InitializePaymentView(generics.CreateAPIView):
    permission_classes = [AllowAny] # Can be called right after registration
    serializer_class = InitializePaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        registration_id = serializer.validated_data["registration_id"]
        
        # We need the user's email, typically available on the registration
        registration = get_object_or_404(
            EventRegistration.objects.select_related("ticket_type"), 
            id=registration_id
        )
        
        if registration.status == EventRegistration.Status.CONFIRMED:
            return Response({"detail": "Registration is already confirmed."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not registration.ticket_type or registration.ticket_type.price <= 0:
            return Response({"detail": "This registration does not require payment."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Generate reference
        reference = str(uuid.uuid4())
        amount = registration.ticket_type.price
        
        email = registration.attendee_email
        if not email and registration.attendee:
            email = registration.attendee.email
            
        if not email:
            return Response({"detail": "Attendee email is required for payment."}, status=status.HTTP_400_BAD_REQUEST)

        # Create Transaction
        transaction = PaymentTransaction.objects.create(
            registration=registration,
            amount=amount,
            reference=reference,
            gateway_name=getattr(settings, "PAYMENT_GATEWAY", "paystack")
        )
        
        try:
            provider = get_payment_provider()
            callback_url = serializer.validated_data.get("callback_url")
            
            kwargs = {}
            if callback_url:
                kwargs["callback_url"] = callback_url
                
            init_data = provider.initialize_payment(
                amount=amount,
                email=email,
                reference=reference,
                **kwargs
            )
            return Response(init_data, status=status.HTTP_200_OK)
        except Exception as e:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.save()
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Payments"])
class VerifyPaymentView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyPaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reference = serializer.validated_data["reference"]
        
        transaction = get_object_or_404(PaymentTransaction, reference=reference)
        
        if transaction.status == PaymentTransaction.Status.SUCCESS:
            return Response({"detail": "Payment already verified.", "status": "success"}, status=status.HTTP_200_OK)
            
        try:
            provider = get_payment_provider()
            verify_data = provider.verify_payment(reference)
            
            if verify_data["status"] == "success":
                transaction.status = PaymentTransaction.Status.SUCCESS
                transaction.save()
                
                # Mark registration as confirmed
                registration = transaction.registration
                registration.status = EventRegistration.Status.CONFIRMED
                registration.save(update_fields=["status"])
                
                return Response({"detail": "Payment successful.", "status": "success"}, status=status.HTTP_200_OK)
            else:
                transaction.status = PaymentTransaction.Status.FAILED
                transaction.save()
                return Response({"detail": "Payment failed.", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
