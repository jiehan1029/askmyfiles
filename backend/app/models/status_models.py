"""
Define schema for the MongoDB collection that holds folder syncing logs.
Defined two models for SyncStatus, beanie (async) and bunnet (sync)
to be used in FastAPI (mostly to read) and Celery (to write) correspondingly.
"""
from beanie import Document as BeanieDocument
from bunnet import Document as BunnetDocument
from datetime import datetime
from typing import Optional


class SyncStatusBeanie(BeanieDocument):
    """Async"""
    folder_path: str
    total_files: int
    processed_files: int
    progress_percent: int
    status: str  # "PENDING", "IN_PROGRESS", "COMPLETE"
    last_synced_at: Optional[datetime] = None
    task_id: Optional[str] = None

    class Settings:
        name = "sync_status"

    class Config:
        arbitrary_types_allowed = True


class SyncStatusBunnet(BunnetDocument):
    """Sync"""
    folder_path: str
    total_files: int
    processed_files: int
    progress_percent: int
    status: str  # "PENDING", "IN_PROGRESS", "COMPLETE"
    last_synced_at: Optional[datetime] = None
    task_id: Optional[str] = None

    class Settings:
        name = "sync_status"

    class Config:
        arbitrary_types_allowed = True

