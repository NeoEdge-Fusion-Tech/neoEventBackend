import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from .database import Base

class PhotoModel(Base):
    __tablename__ = 'photos_photo'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_status = Column(String(20))
    media_file = Column(String(255))

class PhotoFaceModel(Base):
    __tablename__ = 'photos_photoface'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True))
    face_embedding = Column(Vector(512))
    bounding_box = Column(JSONB)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BiometricIdentityModel(Base):
    __tablename__ = 'accounts_biometricidentity'
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(254), unique=True)
    user_id = Column(UUID(as_uuid=True)) 
    face_encoding = Column(Vector(512))

class UserPhotoModel(Base):
    __tablename__ = 'photos_userphoto'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    photo_id = Column(UUID(as_uuid=True))
    event_id = Column(UUID(as_uuid=True))
    confidence_score = Column(Float)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
