# AI Classifier Processing Flow

This document details the architectural methodology behind the `media_classifier` microservice and the Neoevents AI sorting system.

## 1. The Core Philosophy: Logical Partitioning Over Physical Partitioning
When handling massive volumes of high-resolution event photography, the traditional approach of duplicating physical files into user-specific folders (`/user_123/event_456/`) fails catastrophically at scale. 
- ❌ **Moving/Copying files** = Expensive I/O operations and massive storage duplication.
- ❌ **Folder-per-user** = Explodes storage costs and creates synchronization nightmares.

Instead, the Neoevents architecture employs **Logical Partitioning**.
- ✅ **Single Source of Truth**: Images are stored exactly once in an object storage layer (e.g., local disk, S3, or GCS) at `/media/events/gallery/`.
- ✅ **Metadata-Based Sorting**: We use database-driven mapping to "sort" images mathematically.
- ✅ **Infinite Scalability**: Adding 10,000 photos to 500 users only requires adding lightweight database rows, not duplicating gigabytes of binary files.

---

## 2. Storage Strategy (Single Source of Truth)

Images are **NEVER** moved physically after upload. When a vendor uploads a batch of photos, they are written to a single unified directory based on the event:

```text
/event-media/
   /event_id/
       img_001.jpg
       img_002.jpg
       img_003.jpg
```

---

## 3. Metadata-Based Mapping Layer (The Virtual Folder)

Instead of creating physical directories, we rely on a trio of heavily indexed database tables to act as our "Virtual Folder" system.

### Core Data Models

#### 1. The Physical Reference (`Photo`)
Represents the actual file sitting in storage.
```text
Photo Table
-----------
id (UUID)
event_id
uploader_id
media_file (file_url)
ai_status (PENDING, FACES_DETECTED, MAPPED_TO_USERS)
created_at
```

#### 2. The Face Map (`PhotoFace`)
Represents the raw, mathematically extracted data from the AI. If `img_001.jpg` has 3 people in it, 3 records are inserted here.
```text
PhotoFace Table
---------------
id (UUID)
photo_id
face_embedding (512-Dimensional Vector via pgvector)
bounding_box (JSON Array)
confidence (Float)
```

#### 3. The Virtual Folder (`UserPhoto`)
This is the magic table. It acts as the relational bridge that physically links an attendee to a photo, bypassing the need for physical folders.
```text
UserPhoto Table (Virtual Folder)
--------------------------------
id (UUID)
user_id
photo_id
event_id
confidence_score
source (AI | MANUAL)
created_at
```
*(Note: A `unique_together = ('user_id', 'photo_id')` constraint exists here to guarantee absolute deduplication).*

---

## 4. How the Virtual Folder is Accessed
Because we use logical partitioning, retrieving a user's personal gallery is instantaneous and requires zero file operations.

Instead of navigating physical directories like:
`GET /user_123/event_456/`

The Django REST Framework executes a simple `JOIN` query:
```sql
SELECT photo.*
FROM photos_photo p
JOIN photos_userphoto up ON up.photo_id = p.id
WHERE up.user_id = 'user_123'
AND up.event_id = 'event_456';
```
*Boom!* The attendee's personalized gallery is populated instantly. When the attendee hits "Download All", the backend simply queries this table, reads the original files from the single source of truth, and zips them in memory dynamically.

---

## 5. Media Classifier Implementation Flow (FastAPI)

The physical Python implementation of this architecture is built inside the `media_classifier` FastAPI microservice, specifically within `service.py`.

Here is the step-by-step logic executed by the AI Engine:

1. **Batch Reception**: The FastAPI endpoint `/process-batch` receives a lightweight JSON payload containing `photo_ids` and the `event_id`.
2. **Database Query**: FastAPI uses SQLAlchemy to query the Postgres `photos_photo` table to retrieve the exact physical file path (`media_file`) for the given `photo_id`.
3. **Direct File Read**: Bypassing Django and HTTP entirely, FastAPI uses OpenCV to read the physical `.jpg` bytes directly from the shared disk (`/media/events/gallery/...`).
4. **InsightFace Inference**: The `buffalo_s` model scans the image array, detecting $N$ faces.
5. **Data Extraction**: For each detected face, the model extracts a bounding box and a mathematically unique 512-Dimensional `embedding`.
6. **SQL Mapping**: For every single extracted embedding, FastAPI runs the following SQLAlchemy expression against the `pgvector` database extension:
   ```python
   closest_match = db.execute(
       select(BiometricIdentityModel)
       .where(BiometricIdentityModel.face_encoding.l2_distance(embedding) < 1.0)
       .order_by(BiometricIdentityModel.face_encoding.l2_distance(embedding))
       .limit(1)
   ).scalar_one_or_none()
   ```
7. **Virtual Folder Insertion**: If a match is found, FastAPI executes `db.add(new_user_photo)` to insert a record mapping that `user_id` to the `photo_id` within the `UserPhoto` table.
8. **Status Update**: The core `Photo` record is updated to `ai_status = 'MAPPED_TO_USERS'`.
