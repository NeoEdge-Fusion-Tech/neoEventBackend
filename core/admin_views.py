"""
NeoAdmin Internal API Views — restricted to role=ADMIN users.
Provides system stats, event management, gallery views and AI trigger.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, filters
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema


class IsAdminRole(IsAuthenticated):
    """Permission: only users with role == ADMIN may access."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return getattr(request.user, "role", None) == "ADMIN"


# ── System Stats ──────────────────────────────────────────────────────────────

@extend_schema(tags=["NeoAdmin"], summary="System-wide statistics")
class NeoAdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        from accounts.models.user import User
        from events.models import Event
        from photos.models.photo import Photo

        user_counts = User.objects.values("role").annotate(count=Count("id"))
        role_map = {r["role"]: r["count"] for r in user_counts}

        ai_counts = Photo.objects.values("ai_status").annotate(count=Count("id"))
        ai_map = {a["ai_status"]: a["count"] for a in ai_counts}

        total_photos = Photo.objects.count()
        processed = ai_map.get("MAPPED_TO_USERS", 0) + ai_map.get("FACES_DETECTED", 0)
        ai_percent = round((processed / total_photos * 100), 1) if total_photos else 0

        return Response({
            "users": {
                "total": User.objects.count(),
                "admins": role_map.get("ADMIN", 0),
                "owners": role_map.get("OWNER", 0),
                "vendors": role_map.get("VENDOR", 0),
                "attendees": role_map.get("ATTENDEE", 0),
                "validators": role_map.get("VALIDATOR", 0),
            },
            "events": {
                "total": Event.objects.count(),
                "active": Event.objects.filter(status="PUBLISHED").count(),
            },
            "photos": {
                "total": total_photos,
                "ai_processed_percent": ai_percent,
                "by_status": {
                    "PENDING": ai_map.get("PENDING", 0),
                    "FACES_DETECTED": ai_map.get("FACES_DETECTED", 0),
                    "MAPPED_TO_USERS": ai_map.get("MAPPED_TO_USERS", 0),
                    "FAILED": ai_map.get("FAILED", 0),
                },
            },
        })


# ── Events ────────────────────────────────────────────────────────────────────

@extend_schema(tags=["NeoAdmin"], summary="List all events")
class NeoAdminEventListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        from events.models import Event
        from photos.models.photo import Photo

        search = request.query_params.get("search", "")
        events = Event.objects.select_related("owner").order_by("-created_at")
        if search:
            events = events.filter(
                Q(title__icontains=search) | Q(owner__email__icontains=search)
            )

        # Annotate photo counts per event
        photo_counts = (
            Photo.objects.filter(event__in=events)
            .values("event_id")
            .annotate(
                total=Count("id"),
                pending=Count("id", filter=Q(ai_status="PENDING")),
                faces_detected=Count("id", filter=Q(ai_status="FACES_DETECTED")),
                mapped=Count("id", filter=Q(ai_status="MAPPED_TO_USERS")),
                failed=Count("id", filter=Q(ai_status="FAILED")),
            )
        )
        photo_map = {str(p["event_id"]): p for p in photo_counts}

        data = []
        for ev in events:
            pc = photo_map.get(str(ev.id), {})
            data.append({
                "id": str(ev.id),
                "title": ev.title,
                "status": ev.status,
                "start_date": ev.start_date,
                "end_date": ev.end_date,
                "venue_name": ev.venue_name,
                "owner": {
                    "id": str(ev.owner.id),
                    "username": ev.owner.username,
                    "email": ev.owner.email,
                    "full_name": f"{ev.owner.first_name} {ev.owner.last_name}".strip() or ev.owner.username,
                    "phone": ev.owner.phone_number,
                },
                "photos": {
                    "total": pc.get("total", 0),
                    "pending": pc.get("pending", 0),
                    "faces_detected": pc.get("faces_detected", 0),
                    "mapped": pc.get("mapped", 0),
                    "failed": pc.get("failed", 0),
                },
            })

        return Response({"results": data, "count": len(data)})


@extend_schema(tags=["NeoAdmin"], summary="Single event detail with AI stats")
class NeoAdminEventDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, event_id):
        from django.shortcuts import get_object_or_404
        from events.models import Event
        from photos.models.photo import Photo
        from photos.serializers.photo import PhotoSerializer

        event = get_object_or_404(Event.objects.select_related("owner"), id=event_id)

        qs = Photo.objects.filter(event=event).select_related("uploader")

        photographer_id = request.query_params.get("photographer")
        if photographer_id:
            qs = qs.filter(uploader_id=photographer_id)

        ai_stats = qs.values("ai_status").annotate(count=Count("id"))
        ai_map = {s["ai_status"]: s["count"] for s in ai_stats}

        # Photographers list
        photographer_qs = (
            Photo.objects.filter(event=event)
            .values(
                "uploader__id",
                "uploader__username",
                "uploader__first_name",
                "uploader__last_name",
                "uploader__email",
            )
            .annotate(photo_count=Count("id"))
            .order_by("uploader__username")
        )
        photographers = [
            {
                "id": str(p["uploader__id"]),
                "username": p["uploader__username"],
                "full_name": (
                    f"{p['uploader__first_name']} {p['uploader__last_name']}".strip()
                    or p["uploader__username"]
                ),
                "email": p["uploader__email"],
                "photo_count": p["photo_count"],
            }
            for p in photographer_qs
        ]

        serializer = PhotoSerializer(qs, many=True, context={"request": request})

        return Response({
            "event": {
                "id": str(event.id),
                "title": event.title,
                "status": event.status,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "venue_name": event.venue_name,
                "venue_address": getattr(event, "venue_address", ""),
                "owner": {
                    "id": str(event.owner.id),
                    "username": event.owner.username,
                    "email": event.owner.email,
                    "full_name": f"{event.owner.first_name} {event.owner.last_name}".strip() or event.owner.username,
                    "phone": event.owner.phone_number,
                },
            },
            "ai_stats": {
                "PENDING": ai_map.get("PENDING", 0),
                "FACES_DETECTED": ai_map.get("FACES_DETECTED", 0),
                "MAPPED_TO_USERS": ai_map.get("MAPPED_TO_USERS", 0),
                "FAILED": ai_map.get("FAILED", 0),
            },
            "photographers": photographers,
            "photos": serializer.data,
            "total_photos": qs.count(),
        })


@extend_schema(tags=["NeoAdmin"], summary="Trigger AI processing for an event")
class NeoAdminTriggerAIView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, event_id):
        from django.shortcuts import get_object_or_404
        from events.models import Event
        from photos.models.photo import Photo
        from core.sqs import dispatch_task

        event = get_object_or_404(Event, id=event_id)
        pending_photos = Photo.objects.filter(event=event, ai_status="PENDING")

        if not pending_photos.exists():
            return Response({"detail": "No pending photos found for this event.", "count": 0})

        photo_ids = [str(p.id) for p in pending_photos]
        dispatch_task("extract_faces_from_photos", {"photo_ids": photo_ids})

        return Response({
            "status": "success",
            "message": f"AI processing triggered for {len(photo_ids)} photos.",
            "count": len(photo_ids),
        })


# ── Users ─────────────────────────────────────────────────────────────────────

@extend_schema(tags=["NeoAdmin"], summary="List all users")
class NeoAdminUserListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        from accounts.models.user import User

        role_filter = request.query_params.get("role", "")
        search = request.query_params.get("search", "")

        qs = User.objects.order_by("-date_joined")
        if role_filter:
            qs = qs.filter(role=role_filter)
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        data = [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "full_name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "role": u.role,
                "onboarding_status": u.onboarding_status,
                "is_active": u.is_active,
                "date_joined": u.date_joined,
                "phone": u.phone_number,
            }
            for u in qs[:200]  # cap at 200 for safety
        ]

        return Response({"results": data, "count": len(data)})
