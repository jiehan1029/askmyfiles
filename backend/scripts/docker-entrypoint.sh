#!/bin/bash

# Initialize the MongoDB database
echo "Initializing MongoDB..."
poetry run python /app/scripts/init_mongo.py

# Now run the backend server
echo "Starting the backend server..."
poetry run uvicorn --host 0.0.0.0 --port 8000 app.api.main:app --reload
