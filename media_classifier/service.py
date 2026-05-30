import os
import uuid
import cv2
from datetime import datetime
from sqlalchemy import select, update
from insightface.app import FaceAnalysis

from .models import PhotoModel, PhotoFaceModel, BiometricIdentityModel, UserPhotoModel

# We assume this script runs inside media_classifier, so media folder is at ../media/
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(os.path.dirname(os.path.dirname(__file__)), "media"))

# Initialize InsightFace (RetinaFace + ArcFace)
face_app = FaceAnalysis(name="buffalo_s")
face_app.prepare(ctx_id=0, det_size=(640, 640))

def read_image_from_disk(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image not found at {file_path}")
    img = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not decode image at {file_path}")
    return img

def process_reference_image(email: str, image_path: str, db):
    """
    Extracts 512D embedding from a user's reference selfie and updates BiometricIdentity.
    """
    try:
        media_path = os.path.join(MEDIA_ROOT, image_path)
        img = read_image_from_disk(media_path)
        faces = face_app.get(img)
        
        if len(faces) == 0:
            print(f"No face detected in reference image for {email}")
            return
            
        embedding = faces[0].embedding
        
        db.execute(
            update(BiometricIdentityModel)
            .where(BiometricIdentityModel.email == email)
            .values(face_encoding=embedding)
        )
        db.commit()
        print(f"Successfully updated biometric encoding for {email}")
        
    except Exception as e:
        print(f"Error processing reference image for {email}: {e}")
        db.rollback()


def process_and_map_photo(photo_id: str, event_id: str, db):
    """
    Processes a single event photo and maps detected faces to attendees.
    """
    try:
        db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FACES_DETECTED'))
        db.commit()
        
        photo = db.execute(select(PhotoModel).where(PhotoModel.id == photo_id)).scalar_one_or_none()
        if not photo or not photo.media_file:
            raise ValueError(f"No media_file found for photo {photo_id}")
            
        media_path = os.path.join(MEDIA_ROOT, photo.media_file)
        img = read_image_from_disk(media_path)
        faces = face_app.get(img)
        
        if len(faces) == 0:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='MAPPED_TO_USERS'))
            db.commit()
            return
            
        for face in faces:
            bbox = face.bbox.astype(int).tolist()
            embedding = face.embedding
            
            new_face = PhotoFaceModel(
                id=uuid.uuid4(),
                photo_id=photo_id,
                face_embedding=embedding,
                bounding_box=bbox,
                confidence=0.99
            )
            db.add(new_face)
            db.commit()
            
            threshold = 1.0
            closest_match = db.execute(
                select(BiometricIdentityModel)
                .where(BiometricIdentityModel.user_id.isnot(None))
                .where(BiometricIdentityModel.face_encoding.isnot(None))
                .where(BiometricIdentityModel.face_encoding.l2_distance(embedding) < threshold)
                .order_by(BiometricIdentityModel.face_encoding.l2_distance(embedding))
                .limit(1)
            ).scalar_one_or_none()
            
            if closest_match:
                existing_user_photo = db.execute(
                    select(UserPhotoModel)
                    .where(UserPhotoModel.user_id == closest_match.user_id)
                    .where(UserPhotoModel.photo_id == photo_id)
                ).scalar_one_or_none()
                
                if not existing_user_photo:
                    new_user_photo = UserPhotoModel(
                        id=uuid.uuid4(),
                        user_id=closest_match.user_id,
                        photo_id=photo_id,
                        event_id=event_id,
                        confidence_score=0.95,
                        source='AI',
                        created_at=datetime.utcnow()
                    )
                    db.add(new_user_photo)
                    db.commit()
                
        db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='MAPPED_TO_USERS'))
        db.commit()
        
    except Exception as e:
        print(f"Failed to process photo {photo_id}: {e}")
        db.rollback()
        try:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FAILED'))
            db.commit()
        except:
            pass
