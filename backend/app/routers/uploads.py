import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.image_upload import ImageUpload
from app.schemas.image_upload import ImageUploadResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Files are written under static/uploads so they are also served at /static/uploads/...
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
_UPLOAD_SUBDIR = "uploads"
_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}


@router.post("/", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save an uploaded image to disk and record its metadata in the database."""
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    # Build a unique, collision-free name while keeping the original extension.
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    rel_path = os.path.join(_UPLOAD_SUBDIR, str(user.user_id), stored_name)
    abs_path = os.path.join(_STATIC_DIR, rel_path)

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(contents)

    record = ImageUpload(
        user_id=user.user_id,
        filename=file.filename or stored_name,
        content_type=file.content_type,
        file_size=len(contents),
        file_path=rel_path.replace(os.sep, "/"),
        url=f"/static/{rel_path.replace(os.sep, '/')}",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/", response_model=List[ImageUploadResponse])
async def list_uploads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all images uploaded by the current user, newest first."""
    result = await db.execute(
        select(ImageUpload)
        .where(ImageUpload.user_id == user.user_id)
        .order_by(ImageUpload.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{upload_id}", response_model=ImageUploadResponse)
async def get_upload(
    upload_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_owned_upload(upload_id, user, db)
    return record


@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the metadata row and remove the file from disk."""
    record = await _get_owned_upload(upload_id, user, db)

    abs_path = os.path.join(_STATIC_DIR, record.file_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)

    await db.delete(record)
    await db.commit()
    return {"message": "Upload deleted"}


async def _get_owned_upload(upload_id: str, user: User, db: AsyncSession) -> ImageUpload:
    result = await db.execute(
        select(ImageUpload)
        .where(ImageUpload.upload_id == upload_id)
        .where(ImageUpload.user_id == user.user_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")
    return record
