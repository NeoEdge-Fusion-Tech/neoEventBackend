import os
from media_classifier.database import SessionLocal
from media_classifier.models import BiometricIdentityModel, PhotoFaceModel
from sqlalchemy import select

db = SessionLocal()

pf = db.execute(select(PhotoFaceModel).limit(1)).scalar_one_or_none()
if not pf:
    print("No photoface")
    exit()

emb = pf.face_embedding

print(f"Embedding type: {type(emb)}, len: {len(emb)}")

query = (
    select(BiometricIdentityModel)
    .where(BiometricIdentityModel.user_id.isnot(None))
    .where(BiometricIdentityModel.face_encoding.isnot(None))
    .where(BiometricIdentityModel.face_encoding.cosine_distance(emb) < 0.4)
    .order_by(BiometricIdentityModel.face_encoding.cosine_distance(emb))
    .limit(1)
)

try:
    closest = db.execute(query).scalar_one_or_none()
    print(f"Closest match: {closest}")
except Exception as e:
    print(f"Error: {e}")
