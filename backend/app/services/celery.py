"""
Process the given local folders, add embedding and save them into the document store.
"""
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, UTC
from celery import Celery
from bunnet import PydanticObjectId
from celery.signals import worker_process_init
from app.services.pipelines import QDRANT_PREPROCESSING_PIPELINE_W_METADATA
from app.models.status_models import SyncStatusBunnet
from app.services.database import init_mongodb_bunnet, init_qdrant
from app.api.utils import get_files_from_folder


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'celery: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


app = Celery('sync_app',
             broker=os.getenv("REDIS_URL"),
             backend=os.getenv("REDIS_URL"))


@worker_process_init.connect
def init_celery(**kwargs):
    """Initialize data stores globally for all tasks."""
    init_mongodb_bunnet()
    print("Bunnet initiated.")
    init_qdrant()
    print("Qdrant initiated.")


@app.task(bind=True)
def sync_folder(self, folder_path: str, actual_home_dir: str, sync_status_id: str):
    """Sync documents in the given folder"""

    logger.info(f"sync_folder task ID is: {self.request.id}, {sync_status_id=}")

    files = get_files_from_folder(folder_path=folder_path, actual_home_dir=actual_home_dir)

    file_count = len(files)
    processed_count = 0
    skipped_count = 0
    source_files = []
    PROGRESS_INTERVAL = 10  # store every 10%
    milestone = 0
    for index, file_path in enumerate(files):
        try:
            source_file = str(file_path.resolve())
            output = QDRANT_PREPROCESSING_PIPELINE_W_METADATA.run({
                "file_type_router": {
                    "sources": [file_path],
                },
                "add_source_meta": {
                    "source_file": source_file
                }
            })
            # Check if any docs came out of the last component
            # output for a processed file: {'document_writer': {'documents_written': 90}}
            # output for a skipped file: {'file_type_router': {'unclassified': [PosixPath('/host/home/Desktop/Screenshot.png')]}}
            last_component = "document_writer"  # or "document_embedder" if you skip writer
            final_docs = output.get(last_component, {}).get("documents_written", [])
            if final_docs:
                processed_count += 1
                source_files.append(source_file)
            else:
                skipped_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            skipped_count += 1

        logger.info(f"Completed processsing {file_path}")

        # save progress
        current = index+1
        percent = int((current / file_count) * 100)
        self.update_state(state='IN_PROGRESS', meta={'current': current, 'total': file_count, "file": str(file_path)})
        # Only update DB at every 10% milestone
        if percent >= milestone + PROGRESS_INTERVAL or percent == 100:
            milestone = percent
            sync_status = SyncStatusBunnet.find_one(SyncStatusBunnet.id == PydanticObjectId(sync_status_id)).run()
            sync_status.set({
                "total_files": file_count,
                "processed_files": processed_count,
                "skipped_files": skipped_count,
                "source_files": source_files,
                "progress_percent": percent,
                "status": "IN_PROGRESS",
                "last_synced_at": datetime.now(tz=UTC),
            })

    # Final update on complete
    SyncStatusBunnet.find_one(SyncStatusBunnet.id == PydanticObjectId(sync_status_id)).update({
        "$set": {
            "total_files": file_count,
            "processed_files": processed_count,
            "skipped_files": skipped_count,
            "source_files": source_files,
            "progress_percent": 100,
            "status": "COMPLETE",
            "last_synced_at": datetime.now(tz=UTC),
        }
    }).run()
    self.update_state(state='SUCCESS', meta={'current': file_count, 'total': file_count, 'folder_path': folder_path})

    summary = {'current': file_count, 'total': file_count, 'folder_path': folder_path, "task_id": self.request.id, "status": "complete"}
    logger.info(summary)
    return summary
