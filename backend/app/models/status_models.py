"""
Define schema for the MongoDB collection that holds folder syncing logs.
"""
from beanie import Document
from datetime import datetime
from typing import Optional


class SyncStatus(Document):
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
