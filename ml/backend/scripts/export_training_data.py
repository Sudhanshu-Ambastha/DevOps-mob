import asyncio

from nlp.json_files import atomic_write_json, read_json
from nlp.training_data import build_training_rows

from ..config.settings import get_settings
from ..repositories.json_repository import JsonRepository


async def run()->None:
    settings=get_settings()
    dataset=read_json(settings.dataset_path, default={})
    feedback=await JsonRepository(settings.runtime_store_path).list_feedback()
    export=build_training_rows(dataset, feedback)
    target=settings.data_dir/"training_rows.json"
    atomic_write_json(target, export)

    print(f"Wrote {export['row_count']} rows to {target}")


if __name__ == "__main__":
    asyncio.run(run())
