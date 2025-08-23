# app/media/service.py
"""
Utility untuk membuat URL & form fields presign (S3 POST) ke Cloudflare R2.

Dipakai oleh:
- Endpoint /media/presign (jika ada)
- Panel Owner: upload gambar item langsung (server-side presign + direct POST ke R2)

ENV yang dibutuhkan:
- R2_ENDPOINT   : contoh "https://584e687b5fd08a329b103f479582c788.r2.cloudflarestorage.com"
- R2_BUCKET     : contoh "qrmenu-media"
- R2_ACCESS_KEY : Access Key ID
- R2_SECRET_KEY : Secret Access Key

Contoh pakai:
    from .service import presign_upload
    data = presign_upload("image/jpeg", "cafes/1/menu/10/foto.jpg")
    # data = {"url": ..., "fields": {...}, "public_url": ...}
"""

from __future__ import annotations
from typing import Dict, Any
import os
import json
import hmac
import hashlib
import base64
import datetime as dt


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _derive_signing_key(secret_key: str, date_yyyymmdd: str, region: str = "auto", service: str = "s3") -> bytes:
    """
    AWS SigV4 key derivation:
      kDate    = HMAC("AWS4"+secret, date)
      kRegion  = HMAC(kDate, region)
      kService = HMAC(kRegion, service)
      kSigning = HMAC(kService, "aws4_request")
    """
    k_date = _hmac(("AWS4" + secret_key).encode("utf-8"), date_yyyymmdd)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    return k_signing


def _require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def presign_upload(
    content_type: str,
    object_path: str,
    *,
    expires_seconds: int = 10 * 60,           # default 10 menit
    max_file_size: int = 10 * 1024 * 1024,    # default 10 MB
) -> Dict[str, Any]:
    """
    Buat presigned POST untuk upload langsung ke R2.

    Args:
        content_type: MIME type file (contoh: "image/jpeg")
        object_path : path objek di bucket (contoh: "cafes/1/menu/10/foto.jpg")
        expires_seconds: masa berlaku policy
        max_file_size: ukuran maksimum file

    Returns:
        dict dengan keys: url, fields (form), public_url
    """

    # --- ENV ---
    endpoint = _require_env("R2_ENDPOINT").rstrip("/")                # no trailing slash
    bucket = _require_env("R2_BUCKET")
    access_key = _require_env("R2_ACCESS_KEY")
    secret_key = _require_env("R2_SECRET_KEY")

    # --- Key / Paths ---
    key = object_path.lstrip("/")                                     # no leading slash
    post_url = f"{endpoint}/{bucket}"
    public_url = f"{endpoint}/{bucket}/{key}"

    # --- Time / Credential ---
    now = dt.datetime.utcnow()
    date = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    expiration = (now + dt.timedelta(seconds=expires_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")

    algorithm = "AWS4-HMAC-SHA256"
    region = "auto"                          # Cloudflare R2 pakai 'auto'
    credential = f"{access_key}/{date}/{region}/s3/aws4_request"

    # --- Policy (S3 POST form) ---
    conditions = [
        {"bucket": bucket},
        {"key": key},
        {"Content-Type": content_type},
        {"x-amz-algorithm": algorithm},
        {"x-amz-credential": credential},
        {"x-amz-date": amz_date},
        ["content-length-range", 0, max_file_size],
    ]
    policy_doc = {"expiration": expiration, "conditions": conditions}
    policy_b64 = base64.b64encode(json.dumps(policy_doc, separators=(",", ":")).encode("utf-8")).decode("utf-8")

    # --- Signature V4 ---
    signing_key = _derive_signing_key(secret_key, date, region=region, service="s3")
    signature = hmac.new(signing_key, policy_b64.encode("utf-8"), hashlib.sha256).hexdigest()

    fields = {
        "key": key,
        "Content-Type": content_type,
        "x-amz-algorithm": algorithm,
        "x-amz-credential": credential,
        "x-amz-date": amz_date,
        "policy": policy_b64,
        "x-amz-signature": signature,
    }

    return {
        "url": post_url,        # target untuk POST form-data
        "fields": fields,       # pasangan form - WAJIB dipakai persis
        "public_url": public_url,  # URL publik hasil upload
        "expires_at": expiration,
    }
