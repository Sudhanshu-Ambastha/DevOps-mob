from ..config.settings import Settings
from .base import Repository
from .json_repository import JsonRepository
from .mongo_repository import MongoRepository


def build_repository(settings:Settings)->Repository:
    if settings.uses_mongodb:
        return MongoRepository(
            settings.mongodb_uri,
            settings.mongodb_database,
            settings.mongodb_timeout_ms,
            settings.data_dir/"backups"
        )

    return JsonRepository(settings.runtime_store_path)
