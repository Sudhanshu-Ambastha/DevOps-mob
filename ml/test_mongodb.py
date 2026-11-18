
from datetime import datetime, timezone

from pymongo import MongoClient
from backend.config.settings import get_settings


def test_mongodb():

    settings = get_settings()

    # Ensure we are targeting the correct database
    if settings.mongodb_database != "mongodb":
        raise RuntimeError(
            f"Wrong database configured: {settings.mongodb_database}. "
            "Expected: mongodb"
        )

    client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms
    )

    try:
        # Check server connection
        client.admin.command("ping")

        # Connect to the exact database
        db = client["mongodb"]

        # Connect to your existing collection
        collection = db["devops bridge"]

        # Prepare test data
        test_data = {
            "_id": "devbridge-test-001",
            "project": "DevOps",
            "message": "Successfully connected to the correct MongoDB database!",
            "test_type": "database_write_read",
            "status": "success",
            "created_at": datetime.now(timezone.utc)
        }

        # Store test data
        collection.replace_one(
            {"_id": test_data["_id"]},
            test_data,
            upsert=True
        )

        print("Database:", db.name)
        print("Collection:", collection.name)
        print("Document saved successfully!")

        # Read test data
        result = collection.find_one(
            {"_id": "devbridge-test-001"}
        )

        if result:
            print("\nRetrieved document:")
            print(result)
            print("\nSUCCESS: Data is stored in mongodb.devops bridge!")

        else:
            raise RuntimeError("Test document was not found.")

    finally:
        client.close()


if __name__ == "__main__":
    test_mongodb()
