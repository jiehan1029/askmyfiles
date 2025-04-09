"""
Process the given local folders, add embedding and save them into the document store.
"""
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, UTC
from pathlib import Path
from celery import Celery
from bunnet import PydanticObjectId
from celery.signals import worker_process_init
from app.services.pipelines import DEFAULT_PREPROCESSING_PIPELINE
from app.models.status_models import SyncStatusBunnet
from app.services.database import init_mongodb_bunnet, init_qdrant


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'celery: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


app = Celery('sync_app', broker=os.getenv("REDIS_URL"))
app.conf.result_backend = os.getenv("REDIS_URL")


@worker_process_init.connect
def init_celery(**kwargs):
    """Initialize data stores globally for all tasks."""
    init_mongodb_bunnet()
    print("Bunnet initiated.")
    init_qdrant()
    print("Qdrant initiated.")


@app.task(bind=True)
def sync_folder(self, folder_path: str, sync_status_id: str):
    """Sync documents in the given folder"""

    logger.info(f"sync_folder task ID is: {self.request.id}, {sync_status_id=}")

    output_dir = Path(folder_path).expanduser()
    home_dir = os.path.expanduser("~")
    if os.name == "nt":
        home_dir = home_dir.replace("\\", "/")
    if os.getenv("HOST_HOME_DIR"):
        output_dir_str = str(output_dir)
        output_dir_str = output_dir_str.replace(home_dir, "/host/home")
        output_dir = Path(output_dir_str)
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
            sync_status = SyncStatusBunnet.find_one(SyncStatusBunnet.id == PydanticObjectId(sync_status_id)).run()
            sync_status.set({
                "total_files": file_count,
                "processed_files": current,
                "progress_percent": percent,
                "status": "IN_PROGRESS",
                "last_synced_at": datetime.now(tz=UTC),
            })

    # Final update on complete
    SyncStatusBunnet.find_one(SyncStatusBunnet.id == PydanticObjectId(sync_status_id)).update({
        "$set": {
            "total_files": file_count,
            "processed_files": file_count,
            "progress_percent": 100,
            "status": "COMPLETE",
            "last_synced_at": datetime.now(tz=UTC),
        }
    }).run()

    summary = {"processed": file_count, "task_id": self.request.id, "status": "complete"}
    logger.info(summary)
    return summary
