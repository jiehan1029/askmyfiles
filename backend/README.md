### Project Directory
```
backend/              
├── app/
│   ├── api/                   # Http and websocket endpoint that frontend calls
│   ├── models/                # MongoDB ODM - Beanie (async) and Bunnet (sync)
│   └── services/              
│       ├── celery.py                             
│       ├── database.py        # Init MongoDB and Qdrant
│       ├── document_stores.py # Doc store (Haystack)
│       └── pipelines.py       # Pipelines (Haystack)
├── config/qdrant/             # Qdrant config
├── scripts/
├── .env                       
├── ...
frontend/
infra/langfuse/
...
```

* Since Langfuse is used for observability, a `langfuse` repo will be cloned into `/infra` folder under the project root directory (outside `/backend` directory).

### Environment Variables
When running backend with `make backend-up`, you do not need to worry about env vars as all are added in docker compose file(s). Otherwise, take a look at `/backend/.env.example` and add your own `/backend/.env` file if you run API outside docker.

### Other dev notes
**Two ODM for MongoDB**

Beanie and Bunnet are used as ODM for MongoDB at the same time, with two models declared for the same `sync_status` collection. This makes it easier to fullfill the requirement of FastAPI (async) and Celery (sync), keeping the separation of concern for maintenability.

**Inject custom meta field to document**

Pre-processing pipeline injects source file path as metadata so that later it's possible to filter and remove chunks of same source file from the vector database. This is done using Haystack custom component.


