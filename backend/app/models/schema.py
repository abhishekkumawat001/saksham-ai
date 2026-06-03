from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DECIMAL, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(15), unique=True, nullable=False)
    name = Column(String(100))
    preferred_lang = Column(String(20), default='hi')
    role = Column(String(20), default='farmer')  # farmer | merchant | admin
    created_at = Column(DateTime, default=datetime.utcnow)

class Crop(Base):
    __tablename__ = "crops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en = Column(String(100), nullable=False)
    name_hi = Column(String(100))
    category = Column(String(50))
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_en = Column(String(200), nullable=False)
    name_hi = Column(String(200))
    category = Column(String(50)) # fertilizer | pesticide | seed
    brand = Column(String(100))
    is_active = Column(Boolean, default=True)
