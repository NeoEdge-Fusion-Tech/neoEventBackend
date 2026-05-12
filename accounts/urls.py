# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views  import (
    auth,
    password,
    profiles,
)

app_name = "accounts"

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────
    path("account/refresh/", auth.RefreshTokenView.as_view(), name="refresh"),

    path("account/login/", auth.LoginView.as_view(), name="login",),
    path("account/vendor/register/", auth.VendorRegisterView.as_view(), name="vendor-register",),
    path("account/owner/register/", auth.EventOwnerRegisterView.as_view(), name="owner-register",),    
    path("account/attendee/register/", auth.AttendeeRegistrationView.as_view(), name="attendee-register",),
    path("account/logout/", auth.LogoutView.as_view(), name="logout"),

    #  --- User profile management ────────────────────────────────────
    path("me/", profiles.EventOwnerProfileUpdateView.as_view(), name="owner-profile"),
    path("vendor/profile/", profiles.VendorProfileUpdateView.as_view(), name="vendor-profile"),

    # ── User: password management ────────────────────────────────────
    path("auth/password-reset/", password.PasswordResetRequestView.as_view(), name="password_reset"),
    path("auth/password-reset/confirm/", password.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("auth/password/change/", password.PasswordResetRequestView.as_view(), name="password_change"),

]
#     # ── Current user ──────────────────────────────────────────────
#     path("me/", acct_views.UserProfileView.as_view(), name="user_profile"),

#     # ── Admin: user management ────────────────────────────────────
#     path("admin/users/", acct_views.UserListView.as_view(), name="admin_user_list"),
#     path("admin/users/<int:pk>/", acct_views.UserDetailView.as_view(), name="admin_user_detail"),
#     path("admin/users/<int:pk>/approve/", acct_views.ApproveUserView.as_view(), name="admin_approve_user"),





# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView

# from .views import (
#     acct_views,
#     password_views,
# )

# app_name = "account"

# urlpatterns = [
#     path("auth/register/", acct_views.RegisterView.as_view(), name="register"),
#     path("auth/login/", acct_views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
#     path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
#     path("auth/logout/", acct_views.LogoutView.as_view(), name="logout"),

#     # ── User: password management ────────────────────────────────────
#     path("auth/password-reset/", password_views.PasswordResetRequestView.as_view(), name="password_reset"),
#     path("auth/password-reset/confirm/", password_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
#     path("auth/password/change/", password_views.PasswordResetRequestView.as_view(), name="password_change"),

#     # ── Current user ──────────────────────────────────────────────
#     path("me/", acct_views.UserProfileView.as_view(), name="user_profile"),

#     # ── Admin: user management ────────────────────────────────────
#     path("admin/users/", acct_views.UserListView.as_view(), name="admin_user_list"),
#     path("admin/users/<int:pk>/", acct_views.UserDetailView.as_view(), name="admin_user_detail"),
#     path("admin/users/<int:pk>/approve/", acct_views.ApproveUserView.as_view(), name="admin_approve_user"),
# ]

