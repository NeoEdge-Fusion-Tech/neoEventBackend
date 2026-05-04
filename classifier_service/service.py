# photos/service.py
# Image searching and sort service
import os
import numpy as np
import cv2
from django.conf import settings
from insightface.app import FaceAnalysis
from photos.models import Photo, AttendeeGallery, FaceEmbedding

# Initialize once to save memory
app = FaceAnalysis(name="buffalo_l", root=os.path.join(settings.BASE_DIR, 'ml_models'))
app.prepare(ctx_id=-1)

def normalize(vec):
    return vec / (np.linalg.norm(vec) + 1e-6)


def process_attendee_search(user, selfie_path):
    """
    Optimized search using vectorized matrix multiplication.
    """
    # 1. Extract & Normalize Query Embedding
    query_img = cv2.imread(selfie_path)
    query_faces = app.get(query_img)

    if not query_faces:
        return 0
    
    # Normalize the query once
    q_emb = normalize(query_faces[0].embedding).astype(np.float32)

    # 2. Fetch all embeddings for the event in one query
    # We use list() because we need to index into it later
    records = list(FaceEmbedding.objects.filter(
        photo__event=user.active_event
    ).select_related('photo'))

    if not records:
        return 0

    # 3. Vectorized Math (The "Senior" Optimization)
    # Convert list of bytes back into a single N x 512 Matrix
    all_embs = np.array([np.frombuffer(r.embedding, dtype=np.float32) for r in records])
    
    # Cosine similarity is just a dot product if vectors are normalized
    # Result is a 1D array of scores
    similarities = np.dot(all_embs, q_emb)

    # 4. Filter Results
    # Get indices where score >= 0.6
    matched_indices = np.where(similarities >= 0.6)[0]
    
    # Use a set to avoid duplicates (one photo might have multiple matched faces)
    matched_photos = {records[idx].photo for idx in matched_indices}

    # 5. Database Sync
    for photo in matched_photos:
        # Create the gallery link
        AttendeeGallery.objects.get_or_create(
            user=user,
            photo_link=photo,
            defaults={'event': photo.event} # Fixed: passing required event field
        )

        # Update the ManyToMany field on Photo for easy filtering
        if not photo.detected_users.filter(id=user.id).exists():
            photo.detected_users.add(user)

    return len(matched_photos)


def generate_embeddings_for_photo(photo):
    """
    Extract and store embeddings for a photo.
    Runs once per upload.
    """
    img = cv2.imread(photo.image.path)
    faces = app.get(img)

    embeddings = []

    for idx, face in enumerate(faces):
        emb = normalize(face.embedding)

        # Convert numpy → bytes
        emb_bytes = emb.tobytes()

        embeddings.append(
            FaceEmbedding(
                photo=photo,
                embedding=emb_bytes,
                face_index=idx
            )
        )

    FaceEmbedding.objects.bulk_create(embeddings)


# def process_attendee_search(user, selfie_path):
#     query_img = cv2.imread(selfie_path)
#     query_faces = app.get(query_img)

#     if not query_faces:
#         return 0
    
#     q_emb = normalize(query_faces[0].embedding)

#     matched_photos = set()

#     stored_embeddings = FaceEmbedding.objects.filter(
#         photo__event=user.active_event
#     ).select_related('photo')

#     for record in stored_embeddings:
#         g_emb = np.frombuffer(record.embedding, dtype=np.float32).tobytes()

#         g_emb = normalize(g_emb)

#         similarity = np.dot(q_emb, g_emb)

#         if similarity >= 0.6:
#             matched_photos.add(record.photo)

#     for photo in matched_photos:
#         AttendeeGallery.objects.get_or_create(
#             user=user,
#             photo_link=photo,
#             defaults={'event': photo.event} # Pass the event here
#         )

#         if not photo.detected_users.filter(id=user.id).exists():
#             photo.detected_users.add(user)

#     return len(matched_photos)# Generate embedding for photos 

