from fastapi import APIRouter, Depends, UploadFile, File
from app.models.user import User
from app.services.receipt_service import scan_receipt
from app.dependencies import get_current_user

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/scan/")
async def scan(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    contents = await file.read()
    items = await scan_receipt(contents)
    return {"items": items}
