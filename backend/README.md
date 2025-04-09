ODM: beanie
qdrant local dashboard: http://localhost:6333/dashboard


todo: async sync local documents, celery? syncing status update to fe?
todo: manage sync time & version & resync options?


if celery worker doesn't have permission to update /storage folder (qdrant storage), run
sudo chmod -R 777 ./storage
