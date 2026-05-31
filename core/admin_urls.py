from django.urls import path
from .admin_views import (
    NeoAdminStatsView,
    NeoAdminEventListView,
    NeoAdminEventDetailView,
    NeoAdminTriggerAIView,
    NeoAdminUserListView,
)

urlpatterns = [
    path("stats/", NeoAdminStatsView.as_view(), name="neo-admin-stats"),
    path("events/", NeoAdminEventListView.as_view(), name="neo-admin-events"),
    path("events/<uuid:event_id>/", NeoAdminEventDetailView.as_view(), name="neo-admin-event-detail"),
    path("events/<uuid:event_id>/trigger-ai/", NeoAdminTriggerAIView.as_view(), name="neo-admin-trigger-ai"),
    path("users/", NeoAdminUserListView.as_view(), name="neo-admin-users"),
]
