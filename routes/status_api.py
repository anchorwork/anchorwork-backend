"""Lightweight health & settings endpoints.

Provides health check and service status information including uptime, version, and current timestamp.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/status", tags=["status"])
STARTED = datetime.utcnow()
VERSION = "1.0.0"


@router.get("/", summary="Simple health-check")
async def root_status() -> dict:
    """Return service uptime in seconds, version, and current timestamp."""
    uptime = (datetime.utcnow() - STARTED).total_seconds()
    current_time = datetime.utcnow().isoformat() + "Z"
    return {"ok": True, "uptime_s": uptime, "version": VERSION, "timestamp": current_time}
