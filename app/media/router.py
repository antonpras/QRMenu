from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .service import presign_upload
pre = presign_upload("image/jpeg", f"cafes/{cafe.id}/menu/{item.id}/{filename}")
import boto3, uuid
from ..config import settings
router = APIRouter(prefix="/media", tags=["media"])
class PresignRequest(BaseModel):
    content_type: str
    object_path: str | None = None
class PresignResponse(BaseModel):
    url: str
    fields: dict
    public_url: str
def s3client():
    if not all([settings.R2_ENDPOINT, settings.R2_ACCESS_KEY, settings.R2_SECRET_KEY]):
        raise RuntimeError("R2 is not configured")
    return boto3.client(
        "s3",
        endpoint_url=str(settings.R2_ENDPOINT),
        aws_access_key_id=settings.R2_ACCESS_KEY,
        aws_secret_access_key=settings.R2_SECRET_KEY,
        region_name="auto",
    )
@router.post("/presign", response_model=PresignResponse)
def presign(req: PresignRequest):
    try:
        client = s3client()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    key = req.object_path or f"uploads/{uuid.uuid4()}"
    fields = {"Content-Type": req.content_type}
    conditions = [{"Content-Type": req.content_type}]
    presigned_post = client.generate_presigned_post(
        Bucket=settings.R2_BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=600,
    )
    public_url = f"{settings.R2_ENDPOINT}/{settings.R2_BUCKET}/{key}"
    return PresignResponse(url=presigned_post["url"], fields=presigned_post["fields"], public_url=public_url)
