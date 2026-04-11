from __future__ import annotations

from src.config import settings


def build_credentials(raw_value: str | None):
    from google.oauth2 import service_account

    creds_info = settings.resolve_google_credentials(raw_value)
    if not creds_info:
        return None
    return service_account.Credentials.from_service_account_info(creds_info)
