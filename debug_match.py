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

query = (
    select(BiometricIdentityModel, BiometricIdentityModel.face_encoding.cosine_distance(emb).label('distance'))
    .where(BiometricIdentityModel.user_id.isnot(None))
    .where(BiometricIdentityModel.face_encoding.isnot(None))
    .order_by(BiometricIdentityModel.face_encoding.cosine_distance(emb))
    .limit(5)
)

print("Checking matches...")
results = db.execute(query).all()
for match, distance in results:
    print(f"Match found! user_id={match.user_id}, cosine_distance={distance}")
    print(f"Is distance < 0.4? {distance < 0.4}")

db.close()
