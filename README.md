Here’s a clean, production-style README section you can drop into your project.

---

# Neo Events Platform

Neo Events is a scalable event management system built around event creation, vendor coordination (photographers-first), attendee registration, ticketing, and media distribution workflows.

The system is designed with a clear separation of concerns across **events**, **tickets/registrations**, **accounts**, and future **media processing (photos)**.

---

# Authentication System

Neo Events uses **JWT authentication stored in secure HttpOnly cookies**.

## Why this approach was chosen

Instead of storing tokens in `localStorage`, the system uses HttpOnly cookies to improve security and reduce attack surface.

### Key benefits:

* Prevents token access via JavaScript (mitigates XSS attacks)
* Centralized backend control over authentication state
* Automatic cookie inclusion in requests (`credentials: include`)
* Cleaner frontend state management (no manual token handling)

---

## Authentication Flow

1. User logs in via `/auth/login/`
2. Backend issues:

   * Access token (HttpOnly cookie)
   * Refresh token (HttpOnly cookie)
3. Frontend sends requests with credentials enabled
4. Backend validates cookies on every request
5. Token refresh handled transparently

---

# API Documentation (Swagger / ReDoc)

Neo Events provides full API documentation via **drf-spectacular**.

## Available Endpoints

### Schema

```
/api/schema/
```

---

### Swagger UI

```
/api/schema/swagger-ui/
```

Interactive API documentation for testing endpoints directly from the browser.

---

### ReDoc

```
/api/schema/redoc/
```

Clean, structured API documentation for reference and integration.

---

## Django Configuration

```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # ReDoc UI
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
```

---

# Core Modules

## Accounts

* User roles: Admin, Event Owner, Vendor (Photographer), Attendee
* Attendee profiles for event participation and identity mapping
* Vendor onboarding and assignment system

---

## Events

* Event creation and lifecycle management
* Vendor assignment (photographers, videographers, planners)
* Event status control (Draft → Published → Active → Completed)
* Public/private event configuration

---

## Tickets & Registration

* Ticket types (VIP, Regular, etc.)
* Attendee registration system
* QR code generation for entry validation
* Check-in system for event access control
* Registration lifecycle tracking (Pending → Confirmed → Checked-in → Cancelled)

---

## Vendors (Photographers-first design)

* Event-based vendor invitations
* Invitation code system
* Role-based assignment per event
* Confirmation workflow for vendors

---

# Security Design

* JWT stored in HttpOnly cookies
* No reliance on `localStorage` for authentication
* Role-based access control (RBAC)
* Event ownership enforcement for sensitive operations
* Vendor confirmation required before access to event resources

---

# System Design Notes

Neo Events is structured for future scalability into:

* Photo distribution platform (event memories)
* AI-based facial recognition tagging
* Ticket analytics and attendance insights
* Vendor performance tracking
* Event engagement scoring system

---

# Current Focus Areas

* Event CRUD + lifecycle control
* Vendor assignment system (photographers priority)
* Attendee registration and QR-based check-in
* Ticketing system with inventory tracking
* Foundation for photo upload + retrieval system (future module)
