# NeoEvent v1 Architecture Overview

This document outlines the core architecture, roles, API structure, and developer tooling for the NeoEvent platform.

## 1. User Roles & Authentication

| Role     | Public Signup? | Notes                  |
| -------- | -------------- | ---------------------- |
| ATTENDEE | YES            | Fastest onboarding.    |
| OWNER    | YES            | Requires approval.     |
| VENDOR   | YES            | Requires approval.     |
| ADMIN    | NO             | Internal creation only.|

### Auth API Structure
```
AUTH
├── register
│   ├── attendee
│   ├── owner
│   └── vendor
│
├── login
├── logout
├── refresh
├── verify-email
├── resend-verification
├── forgot-password
├── reset-password
│
├── onboarding
│   ├── complete-profile
│   ├── upload-headshot
│   ├── vendor-portfolio
│   └── payout-setup
│
└── internal
    └── admin-create
```

## 2. Core API Modules (Django REST Framework)

### `api/events/`
- Event CRUD operations.
- Vendor invitations and assignments.
- Participant lists and check-in tracking.

### `api/photos/`
- Event galleries (Attendee and Event Owner views).
- Image uploads (direct S3 uploads/local backups).
- AI Processing status reporting (`PENDING`, `FACES_DETECTED`, `MAPPED_TO_USERS`, `FAILED`).
- Zip downloads and pre-signed S3 URLs.

### `api/neo-admin/` (Internal Portal)
*Protected by `IsAdminRole` (`role="ADMIN"`)*
- `/stats/`: System-wide metrics (users, events, AI processing progress).
- `/events/`: All events across the platform with owner details and photo counts.
- `/events/<id>/`: Specific event details + photographer distribution.
- `/events/<id>/trigger-ai/`: Manual trigger for AI processing of `PENDING` photos via SQS/Celery.
- `/users/`: Directory of all system users.

## 3. Asynchronous Tasks & Microservices

- **Celery / SQS Worker (`sqs_worker.py`)**: Consumes background tasks such as sending transactional emails and processing batch photo jobs.
- **FastAPI Classifier Service**: A dedicated FastAPI Python microservice running on port `8002`. Handles heavy GPU/CPU workloads for vectorizing faces and mapping them to user headshots using pgvector.
- **Email Service (`services/emails.py`)**: Centralized email handler using unified templates (`base_email.html`, `welcome_email.html`, `vendor_invitation.html`, etc.) powered by standard Django backends (with an extensible architecture to Resend/SMTP).

## 4. Local Development

We use convenient shell scripts to bootstrap the development environments without manually managing commands:

### Backend Startup
```bash
cd neoEventBackend
./start_dev.sh
```
*What it does: Uses Docker Compose (`docker-compose.dev.yml`) to orchestrate PostgreSQL (pgvector), Redis, Celery, the Django backend (`runserver`), and the FastAPI microservice.*

### Frontend Startup
```bash
cd neoEventUsers
./start_dev.sh
```
*What it does: Runs `npm install` (if necessary) and boots the Vite React development server on port `5173`.*

## 5. Frontend Architecture (React / Vite)

- **Routing (`react-router-dom`)**: Standard routes protected by a `<ProtectedRoute allowedRoles={[...]} />` component.
- **State & Networking**:
  - Global authentication state managed in `AuthContext.jsx`.
  - Axios interceptor (`api/axios.js`) automatically refreshes expired JWT tokens and manages `Authorization` headers.
- **Key Dashboards**:
  - **Attendee**: Tickets, check-ins, personal AI-filtered gallery.
  - **Organizer**: Event configuration, attendee tracking, check-ins, vendor invites, and the **Event Owner Gallery** with per-photographer filtering.
  - **Vendor/Photographer**: Portfolio setup, event applications, and photo batch uploading.
  - **NeoAdmin (`/neo-admin`)**: Top-level system administration portal for superusers.