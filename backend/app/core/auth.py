"""
Simple admin authentication for protected dashboard APIs.
"""

from typing import Optional

from fastapi import Header, HTTPException, status

# Import settings to access ADMIN_TOKEN
from .config import settings


def issue_admin_token(username: str) -> str:
    """Return the configured admin token (ignores username)."""
    return settings.ADMIN_TOKEN


def revoke_admin_token(token: str) -> None:
    """Revoke operation is a no-op since token is static."""
    pass


def is_valid_admin_token(token: Optional[str]) -> bool:
    """Validate token against the configured ADMIN_TOKEN."""
    if not token:
        return False
    return token == settings.ADMIN_TOKEN


async def require_admin(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not is_valid_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
        )
    return token
