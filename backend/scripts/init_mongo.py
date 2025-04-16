import asyncio
from datetime import UTC, datetime
from app.models.chat_models import User
from app.services.database import init_mongodb_beanie


# Function to initialize database
async def init_db():
    try:
        client, db = await init_mongodb_beanie()

        db_collection_names = await db.list_collection_names()
        print(f"Found {db_collection_names=}")

        # Check if the collection already exists and add a document if necessary
        if "users" not in db_collection_names:
            print("Collection 'users' does not exist. Initializing with some data.")
            message = User(username="appuser", created_at=datetime.now(tz=UTC))
            await message.insert()
            print("First User record inserted!")
        else:
            print("Collection 'users' already exists. Skipping initialization.")
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    asyncio.run(init_db())
