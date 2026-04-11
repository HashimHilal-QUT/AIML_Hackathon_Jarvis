from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from src.config import LOCAL_MEDIA_DIR, settings


async def upload_audio(audio_bytes: bytes, filename: str) -> str:
    if settings.azure_storage_connection_string:
        from azure.storage.blob import (
            BlobSasPermissions,
            BlobServiceClient,
            ContentSettings,
            generate_blob_sas,
        )

        blob_service = BlobServiceClient.from_connection_string(settings.azure_storage_connection_string)
        container = blob_service.get_container_client(settings.azure_storage_container)
        container.upload_blob(
            name=filename,
            data=audio_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type="audio/mpeg"),
        )

        account_name = blob_service.account_name
        account_key = blob_service.credential.account_key
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=settings.azure_storage_container,
            blob_name=filename,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(UTC) + timedelta(hours=settings.azure_sas_expiry_hours),
        )
        return f"{container.url}/{filename}?{sas_token}"

    safe_name = f"{uuid4().hex}-{Path(filename).name}"
    destination = LOCAL_MEDIA_DIR / safe_name
    destination.write_bytes(audio_bytes)
    return f"{settings.local_media_url_base}/{safe_name}"
