# Neoevents Platform - Backend 📸🤖

Neoevents is a scalable, AI-powered event management system built around event creation, vendor coordination, attendee registration, ticketing, and massive media distribution workflows.

It utilizes advanced Deep Learning facial recognition (`InsightFace`) and high-performance vector databases (`pgvector`) to automatically sort, match, and distribute thousands of event photos directly to attendees via "Virtual Folders."

## 📚 Official Documentation

Before diving into the codebase, we highly recommend reading the core technical documents:

1. [Product Requirements Document (PRD)](docs/neoevents_prd.md): The overarching business logic, user personas, and strict role-based access control.
2. [System Architecture](docs/system_architecture.md): The "Bible". Explains how the microservices communicate, why the AI Engine is decoupled from Django, and the Direct-to-S3 bulk upload strategies.
3. [AI Classifier Engine](docs/ai_classifier.md): Deep dive into the math and logic behind the `FastAPI + InsightFace + pgvector` microservice.

---

## 🏗️ Architecture Overview

The backend uses a heavily decoupled, microservice-inspired architecture:

- **Orchestrator (Django REST Framework)**: Handles Auth, Database ORM, and Business Logic.
- **AI Engine (FastAPI)**: A standalone microservice that mathematically analyzes images using OpenCV and InsightFace.
- **Task Queue (Celery + Redis)**: Bridges Django and FastAPI asynchronously so massive photo batches never cause HTTP timeouts.
- **Database (PostgreSQL + pgvector)**: Stores user data alongside 512-Dimensional facial vectors for native SQL-based similarity searches.

---

## 🚀 Engineer Setup Guide: Local Development

We have designed a fully isolated local development environment using Docker Compose. This ensures you can test everything (including massive photo uploads) entirely offline without touching AWS.

### 1. Configure the Environment
Ensure you have the `.env.dev` file configured in the `neoEventBackend` folder. Specifically, `USE_S3=False` ensures that uploads bypass AWS and save directly to your local Docker `media_volume`.

### 2. Start the Backend Infrastructure
The backend relies on Docker to boot up Postgres, Redis, Django, Celery, and FastAPI simultaneously. It mounts a shared local volume so all services can read the uploaded images.

Open your terminal and navigate to the backend directory:
```bash
cd neoEventBackend
```

Start the cluster using the provided start script (in detached mode):
```bash
./start_dev.sh -d
```
*(Alternatively, you can manually run `docker-compose -f docker-compose.dev.yml up --build -d`)*

*Note: Both Django and FastAPI are configured for hot-reloading using host-volume mounting. You can edit Python files and the containers will restart automatically.*

### 3. Verify the Setup
The API should now be running at `http://127.0.0.1:8000/`. You can view the swagger docs at `http://127.0.0.1:8000/api/schema/swagger-ui/`.

*(Note: If you need to run individual python scripts or manage migrations manually, you can run `docker-compose -f docker-compose.dev.yml exec django python manage.py migrate`)*

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

## Authentication Flow
1. User logs in via `/auth/login/`
2. Backend issues Access token and Refresh token (HttpOnly cookies)
3. Frontend sends requests with credentials enabled
4. Backend validates cookies on every request
5. Token refresh handled transparently

---

# API Documentation (Swagger / ReDoc)

Neo Events provides full API documentation via **drf-spectacular**.

### Swagger UI
```
/api/schema/swagger-ui/
```
Interactive API documentation for testing endpoints directly from the browser.

### ReDoc
```
/api/schema/redoc/
```
Clean, structured API documentation for reference and integration.

---

# Core Modules

## Accounts
* User roles: Admin, Event Owner, Vendor (Photographer), Attendee
* Attendee profiles for event participation and identity mapping
* Vendor onboarding and assignment system

## Events
* Event creation and lifecycle management
* Vendor assignment (photographers, videographers, planners)
* Event status control (Draft → Published → Active → Completed)
* Public/private event configuration

## Tickets & Registration
* Ticket types (VIP, Regular, etc.)
* Attendee registration system
* QR code generation for entry validation
* Check-in system for event access control
* Registration lifecycle tracking

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
