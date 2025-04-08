"""
Process the given local folders, add embedding and save them into the document store.
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from datetime import datetime, UTC
from beanie import PydanticObjectId
from pathlib import Path
from celery import Celery
from app.services.pipelines import DEFAULT_PREPROCESSING_PIPELINE
from app.models.status_models import SyncStatus
from app.services.database import init_mongodb, init_qdrant


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'celery: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


app = Celery('sync_app', broker=os.getenv("REDIS_URL"))
app.conf.result_backend = os.getenv("REDIS_URL")


async def init_celery():
    """Initialize data stores globally for all tasks."""
    await init_mongodb()
    print("Beanie initiated.")
    init_qdrant()
    print("Qdrant initiated.")


def on_after_configure(sender, **kwargs):
    """This function is called after Celery configuration."""
    # make sure there is a running event loop first
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If event loop is already running, create a task
        asyncio.create_task(init_celery())
    else:
        # If no event loop is running, run a new one
        asyncio.run(init_celery())  # This creates and runs a new event loop


# Call the initialization function during worker startup
app.on_after_configure.connect(on_after_configure)


@app.task(bind=True)
def sync_folder(self, folder_path: str, sync_status_id: str):
    return asyncio.run(_sync_folder_impl(self, folder_path, sync_status_id))


async def _sync_folder_impl(self, folder_path: str, sync_status_id: str):
    """Sync documents asynchronously."""

    logger.info(f"sync_folder task ID is: {self.request.id}")

    output_dir = Path(folder_path).expanduser()
    home_dir = os.path.expanduser("~")
    if os.name == "nt":
        home_dir = home_dir.replace("\\", "/")
    if os.getenv("HOST_HOME_DIR"):
        output_dir = output_dir.replace(home_dir, "/host/home")
    logger.info(f"{output_dir=} for {os.name=} and {folder_path=}")

    results = []
    files = [f for f in output_dir.glob("**/*") if f.is_file()]
    file_count = len(files)
    PROGRESS_INTERVAL = 10  # store every 10%
    milestone = 0
    for index, file_path in enumerate(files):
        try:
            DEFAULT_PREPROCESSING_PIPELINE.run({
                "file_type_router": {
                    "sources": [file_path]
                }
            })
            results.append({"filename": file_path, "timestamp": datetime.now(tz=UTC).timestamp()})
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

        logger.info(f"Completed processsing {file_path}")

        # save progress
        current = index+1
        percent = int((current / file_count) * 100)
        self.update_state(state='PROGRESS', meta={'current': current, 'total': file_count, "file": str(file_path)})
        # Only update DB at every 10% milestone
        if percent >= milestone + PROGRESS_INTERVAL or percent == 100:
            milestone = percent
            await SyncStatus.find_one(SyncStatus.id == sync_status_id).update({
                "$set": {
                    "processed_files": current,
                    "progress_percent": percent,
                    "status": "IN_PROGRESS",
                    "last_synced_at": datetime.now(tz=UTC),
                }
            })

    # Final update on complete
    # await SyncStatus.find_one(SyncStatus.id == sync_status_id).update({
    sync_status = await SyncStatus.get(sync_status_id)
    if sync_status:
        await sync_status.update({
            "$set": {
                "processed_files": file_count,
                "progress_percent": 100,
                "status": "COMPLETE",
                "last_synced_at": datetime.now(tz=UTC),
            }
        })

    summary = {"processed": file_count, "task_id": self.request.id, "status": "complete"}
    logger.info(summary)
    return summary
