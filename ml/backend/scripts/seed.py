import argparse
import asyncio
import sys

from nlp.json_files import read_json

from ..config.settings import get_settings
from ..repositories.json_repository import JsonRepository


def parse_arguments()->argparse.Namespace:
    parser=argparse.ArgumentParser(description="Seed the DevBridge demo store.")
    parser.add_argument("--reset", action="store_true", help="delete all runtime data, after making a backup")
    parser.add_argument("--yes", action="store_true", help="confirm --reset")

    return parser.parse_args()


async def run(arguments:argparse.Namespace)->int:
    settings=get_settings()
    dataset=read_json(settings.dataset_path, default=None)

    if dataset is None:
        print(f"Dataset not found: {settings.dataset_path}")
        return 1

    repository=JsonRepository(settings.runtime_store_path)

    if arguments.reset:
        if not arguments.yes:
            print("--reset removes all runtime submissions. Add --yes to confirm.")
            return 1

        summary=await repository.reset(dataset)
        print(f"Reset complete. Backup: {summary['backup']}")
    else:
        summary=await repository.seed(dataset)

    print(f"Dataset version: {summary['dataset_version']}")
    print(f"Added:   {summary['added']}")
    print(f"Skipped: {summary['skipped']}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run(parse_arguments())))
