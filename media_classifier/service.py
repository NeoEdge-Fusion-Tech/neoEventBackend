import os
import uuid
import cv2
import urllib.request
import numpy as np
from datetime import datetime
from sqlalchemy import select, update, cast, String
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

def read_image_from_url(image_url: str):
    try:
        # User-Agent is sometimes needed to avoid 403 Forbidden
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=15)
        arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Could not decode image at {image_url}")
        return img
    except Exception as e:
        raise ValueError(f"Failed to fetch or decode image from {image_url}: {e}")

def process_reference_image(email: str, image_url: str, db, user_id: str = None):
    """
    Extracts 512D embedding from a user's reference selfie and updates BiometricIdentity.
    """
    try:
        print(f"DEBUG: image_url passed in = {image_url}")
        print(f"DEBUG: __file__ inside service.py = {__file__}")
        print(f"DEBUG: MEDIA_ROOT = {MEDIA_ROOT}")
        
        if image_url.startswith("http://") or image_url.startswith("https://"):
            img = read_image_from_url(image_url)
        else:
            clean_url = image_url
            if clean_url.startswith("/media/"):
                clean_url = clean_url.replace("/media/", "", 1)
            elif clean_url.startswith("media/"):
                clean_url = clean_url.replace("media/", "", 1)
            clean_url = clean_url.lstrip("/")
            
            media_path = os.path.join(MEDIA_ROOT, clean_url)
            img = read_image_from_disk(media_path)
            
        faces = face_app.get(img)
        
        if len(faces) == 0:
            print(f"No face detected in reference image for {email}")
            return
            
        embedding = faces[0].embedding
        
        values_to_update = {"face_encoding": embedding}
        if user_id:
            values_to_update["user_id"] = user_id
            
        db.execute(
            update(BiometricIdentityModel)
            .where(BiometricIdentityModel.email == email)
            .values(**values_to_update)
        )
        db.commit()
        print(f"Successfully updated biometric encoding for {email}")
        
    except Exception as e:
        print(f"Error processing reference image for {email}: {e}")
        db.rollback()


def process_and_map_photo(photo_id: str, media_url: str, event_id: str, db, consented_user_ids: list = None):
    """
    Processes a single event photo and maps detected faces to attendees.
    """
    try:
        db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FACES_DETECTED'))
        db.commit()
        
        if media_url.startswith("http://") or media_url.startswith("https://"):
            img = read_image_from_url(media_url)
        else:
            clean_file = media_url
            if clean_file.startswith("/media/"):
                clean_file = clean_file.replace("/media/", "", 1)
            elif clean_file.startswith("media/"):
                clean_file = clean_file.replace("media/", "", 1)
            clean_file = clean_file.lstrip("/")
            
            media_path = os.path.join(MEDIA_ROOT, clean_file)
            img = read_image_from_disk(media_path)
            
        faces = face_app.get(img)
        
        mapped_any = False
        
        if len(faces) == 0:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FAILED'))
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
                confidence=0.99,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_face)
            db.commit()
            
            threshold = 0.4
            
            query = select(BiometricIdentityModel).where(BiometricIdentityModel.user_id.isnot(None)).where(BiometricIdentityModel.face_encoding.isnot(None))
            
            if consented_user_ids is not None:
                query = query.where(cast(BiometricIdentityModel.user_id, String).in_(consented_user_ids))
                
            closest_match = db.execute(
                query
                .where(BiometricIdentityModel.face_encoding.cosine_distance(embedding) < threshold)
                .order_by(BiometricIdentityModel.face_encoding.cosine_distance(embedding))
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
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_user_photo)
                    db.commit()
                mapped_any = True
                
        if mapped_any:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='MAPPED_TO_USERS'))
        elif len(faces) > 0:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FACES_DETECTED'))
        else:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FAILED')) # or keep PENDING, but FAILED since no faces found
            
        db.commit()
        
    except Exception as e:
        print(f"Failed to process photo {photo_id}: {e}")
        db.rollback()
        try:
            db.execute(update(PhotoModel).where(PhotoModel.id == photo_id).values(ai_status='FAILED'))
            db.commit()
        except:
            pass
