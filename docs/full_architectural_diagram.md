# Neoevents Full Architectural Diagram

Below is the complete, high-definition architectural map of the Neoevents Platform. This diagram illustrates the physical infrastructure, network layers, application services, and data persistence layers.

```mermaid
flowchart TB
    %% Styling
    classDef client fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    classDef django fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff
    classDef celery fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:#333
    classDef fastapi fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff
    classDef db fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:#fff
    classDef storage fill:#34495e,stroke:#2c3e50,stroke-width:2px,color:#fff
    classDef redis fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#fff

    %% Subgraphs for Organization
    subgraph Clients["Frontend Clients React or Next.js"]
        A_UI[Attendee Dashboard]:::client
        O_UI[Event Organizer Dashboard]:::client
        V_UI[Vendor or Photographer Portal]:::client
    end

    subgraph Django_Monolith["Core Backend Django REST"]
        API_Gateway[API Routers and Auth]:::django
        Auth_App[Accounts App]:::django
        Events_App[Events App]:::django
        Photos_App[Photos App]:::django
    end

    subgraph Async_Workers["Task Queues"]
        Redis[(Redis Message Broker)]:::redis
        Celery_Workers[Celery Workers]:::celery
    end

    subgraph AI_Engine["AI Microservice FastAPI"]
        FastAPI_Router[FastAPI Router]:::fastapi
        Service_Logic[AI Service Logic]:::fastapi
        InsightFace[InsightFace buffalo_s Model]:::fastapi
        SQLAlchemy[SQLAlchemy ORM]:::fastapi
    end

    subgraph Data_Persistence["Persistence Layer"]
        PG_DB[(PostgreSQL)]:::db
        PG_Vector[[pgvector Extension]]:::db
        File_System[(Shared Local Disk or S3)]:::storage
    end

    %% Client to Django Connections
    A_UI -->|GET /download-zip| Photos_App
    A_UI -->|POST /biometrics| Auth_App
    O_UI -->|POST /notify-attendees| Photos_App
    V_UI -->|POST /upload batch images| Photos_App

    %% Internal Django Routing
    API_Gateway --> Auth_App
    API_Gateway --> Events_App
    API_Gateway --> Photos_App

    %% Django to Storage & DB
    Auth_App -->|Save Selfie| File_System
    Photos_App -->|Save Event Media| File_System
    Django_Monolith -->|Read or Write ORM| PG_DB

    %% Django to Async Queue
    Auth_App -->|Task process_biometric_image| Redis
    Photos_App -->|Task extract_faces_from_photos| Redis
    Photos_App -->|Task notify_users_of_mapped_gallery| Redis

    %% Async Worker Operations
    Redis -->|Consume Task| Celery_Workers
    Celery_Workers -->|Trigger Notification Emails| A_UI
    Celery_Workers -->|POST /process-reference payload| FastAPI_Router
    Celery_Workers -->|POST /process-batch payload| FastAPI_Router

    %% FastAPI Internal Logic
    FastAPI_Router --> Service_Logic
    Service_Logic -->|Extract 512D Vector| InsightFace
    Service_Logic -->|Direct Query| SQLAlchemy

    %% FastAPI to Data Layer
    Service_Logic -->|Read Image Bytes Direct| File_System
    SQLAlchemy -->|INSERT PhotoFace / UserPhoto| PG_DB
    SQLAlchemy -->|L2 Distance Math| PG_Vector
    PG_Vector --> PG_DB
```

### Component Legend
* **Blue (Clients)**: The user-facing interfaces where Attendee, Vendors, and Organizers interact with the system.
* **Green (Django)**: The primary REST API. Handles permissions, session tokens, and business logic.
* **Orange/Yellow (Task Queues)**: The Celery and Redis stack that offloads heavy lifting from Django so the user doesn't experience hanging requests.
* **Red (FastAPI)**: The dedicated, isolated Python microservice that strictly handles InsightFace detection and vector math.
* **Purple/Dark Blue (Persistence)**: The hard storage. The PostgreSQL database (enhanced with `pgvector`) and the physical file storage where the heavy `.jpg` files live.
