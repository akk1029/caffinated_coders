import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class ImageUpload(Base):
    __tablename__ = "image_uploads"

    upload_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    filename = Column(String, nullable=False)          # original filename from the client
    content_type = Column(String, nullable=True)       # e.g. "image/png"
    file_size = Column(Integer, nullable=False)         # size in bytes
    file_path = Column(String, nullable=False)          # path on disk relative to the static dir
    url = Column(String, nullable=False)               # public URL served under /static
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploads")
