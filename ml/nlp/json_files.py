import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

REPLACE_ATTEMPTS=8
REPLACE_DELAY_SECONDS=0.05


def read_json(path:Path, default:Any=None)->Any:
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return default
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS-1:
                raise

            time.sleep(REPLACE_DELAY_SECONDS)

    return default


def atomic_write_json(path:Path, payload:Any, indent:int|None=2)->None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name=tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=indent)
            file.flush()
            os.fsync(file.fileno())

        _replace_with_retry(temp_name, path)
    except BaseException:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

        raise


def _replace_with_retry(source:str, target:Path)->None:
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS-1:
                raise

            time.sleep(REPLACE_DELAY_SECONDS)
