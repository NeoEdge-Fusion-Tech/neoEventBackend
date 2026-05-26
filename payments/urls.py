from django.urls import path
from .views import InitializePaymentView, VerifyPaymentView

urlpatterns = [
    path("initialize/", InitializePaymentView.as_view(), name="payment-initialize"),
    path("verify/", VerifyPaymentView.as_view(), name="payment-verify"),
]
