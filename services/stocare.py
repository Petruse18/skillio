"""Unde stau pozele: în cloud (Vultr Object Storage, compatibil S3) sau local, în data/uploads.

În baza de date, o poză e un text scurt („referință”):
    s3:uploads/img_ab12.jpg    -> în bucket-ul S3
    local:img_ab12.jpg         -> în data/uploads
    /cale/veche/img_ab12.jpg   -> format vechi (cale completă); îl citim în continuare

Pentru cloud, pune în .env: S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY.
Bucket-ul rămâne privat: browserul primește linkuri semnate, valabile o oră.
"""
import base64
import logging
import mimetypes
import threading
import time
from pathlib import Path

from core import config

log = logging.getLogger("skillio.stocare")
_client = None
_lock = threading.Lock()
_cache_url: dict[str, tuple[float, str]] = {}
_cache_bytes: dict[str, bytes] = {}


def activ() -> bool:
    return bool(config.S3_ENDPOINT and config.S3_BUCKET and config.S3_ACCESS_KEY and config.S3_SECRET_KEY)


def _s3():
    global _client
    with _lock:
        if _client is None:
            import boto3
            from botocore.config import Config
            _client = boto3.client("s3", endpoint_url=config.S3_ENDPOINT, region_name=config.S3_REGION,
                                   aws_access_key_id=config.S3_ACCESS_KEY,
                                   aws_secret_access_key=config.S3_SECRET_KEY,
                                   config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=15))
        return _client


def _mime(nume):
    return mimetypes.guess_type(nume)[0] or "image/jpeg"


def salveaza(date: bytes, nume: str) -> str:
    """Salvează poza și întoarce referința de pus în baza de date."""
    if activ():
        cheie = f"uploads/{nume}"
        try:
            _s3().put_object(Bucket=config.S3_BUCKET, Key=cheie, Body=date, ContentType=_mime(nume))
            _cache_bytes[f"s3:{cheie}"] = date
            return f"s3:{cheie}"
        except Exception as e:  # dacă cloud-ul nu merge, nu pierdem poza: o păstrăm local
            log.warning("Upload S3 eșuat, salvez local: %s", e)
    config.UPLOADS.mkdir(parents=True, exist_ok=True)
    (config.UPLOADS / nume).write_bytes(date)
    return f"local:{nume}"


def _cale_locala(ref: str) -> Path | None:
    if ref.startswith("local:"):
        return config.UPLOADS / ref[6:]
    p = Path(ref)
    if p.exists():
        return p
    alt = config.UPLOADS / Path(ref.replace("\\", "/")).name    # cale de pe alt calculator
    return alt if alt.exists() else None


def citeste(ref: str | None) -> bytes | None:
    if not ref:
        return None
    if ref.startswith("s3:"):
        if ref in _cache_bytes:
            return _cache_bytes[ref]
        if not activ():
            return None
        try:
            date = _s3().get_object(Bucket=config.S3_BUCKET, Key=ref[3:])["Body"].read()
        except Exception as e:
            log.warning("Nu pot citi %s: %s", ref, e)
            return None
        if len(_cache_bytes) > 300:
            _cache_bytes.clear()
        _cache_bytes[ref] = date
        return date
    p = _cale_locala(ref)
    try:
        return p.read_bytes() if p else None
    except OSError:
        return None


def url(ref: str | None) -> str:
    """Adresa de pus într-un <img src="...">: link semnat (cloud) sau data: URI (local)."""
    if not ref:
        return ""
    if ref.startswith("s3:") and activ():
        acum = time.time()
        c = _cache_url.get(ref)
        if c and c[0] > acum:
            return c[1]
        try:
            u = _s3().generate_presigned_url("get_object", Params={"Bucket": config.S3_BUCKET, "Key": ref[3:]},
                                             ExpiresIn=3600)
        except Exception as e:
            log.warning("Nu pot semna %s: %s", ref, e)
            return ""
        _cache_url[ref] = (acum + 3000, u)
        return u
    date = citeste(ref)
    if not date:
        return ""
    return f"data:{_mime(ref.split(':', 1)[-1])};base64,{base64.b64encode(date).decode()}"
