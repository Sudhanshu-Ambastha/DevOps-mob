import argparse
import asyncio
import sys

from ..config.settings import get_settings
from ..repositories.factory import build_repository
from ..services.seed_service import ensure_demo_accounts, load_seed_dataset


def parse_arguments()->argparse.Namespace:
    parser=argparse.ArgumentParser(description="Seed the DevBridge demo data.")
    parser.add_argument("--reset", action="store_true", help="delete all stored data, after making a backup")
    parser.add_argument("--yes", action="store_true", help="confirm --reset")
    parser.add_argument("--no-demo-accounts", action="store_true", help="skip the three demo logins")

    return parser.parse_args()


async def run(arguments:argparse.Namespace)->int:
    settings=get_settings()
    dataset=load_seed_dataset(settings)

    if not dataset.get("problems"):
        print(f"Dataset not found: {settings.dataset_path}")
        return 1

    if arguments.reset and not arguments.yes:
        print("--reset removes every stored submission. Add --yes to confirm.")
        return 1

    repository=build_repository(settings)

    try:
        await repository.prepare()
        target=settings.mongodb_database if settings.uses_mongodb else settings.runtime_store_path
        print(f"Store: {settings.data_store} ({target})")

        if arguments.reset:
            summary=await repository.reset(dataset)
            print(f"Reset complete. Backup: {summary['backup']}")
        else:
            summary=await repository.seed(dataset)

        print(f"Added:   {summary['added']}")
        print(f"Skipped: {summary['skipped']}")

        if not getattr(arguments, "no_demo_accounts", False) and not settings.is_production:
            emails=await ensure_demo_accounts(repository, settings)
            print(f"Demo accounts ready: {', '.join(emails)}")
    finally:
        await repository.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run(parse_arguments())))
