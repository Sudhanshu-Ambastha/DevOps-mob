import copy
import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

from filelock import FileLock, Timeout

from nlp.json_files import atomic_write_json, read_json

SCHEMA_VERSION=1
LOCK_TIMEOUT_SECONDS=10

COLLECTIONS=(
    "users",
    "problems",
    "community_reports",
    "relationships",
    "upvotes",
    "follows",
    "comments",
    "solutions",
    "match_sessions",
    "ai_feedback",
    "srs_documents"
)

Result=TypeVar("Result")


class StoreCorruptedError(Exception):
    pass


class StoreBusyError(Exception):
    pass


def empty_state()->dict[str, Any]:
    state:dict[str, Any]={"schema_version":SCHEMA_VERSION,"seeded_dataset_version":None}

    for name in COLLECTIONS:
        state[name]=[]

    return state


class JsonStore:
    def __init__(self, path:Path):
        self.path=path
        self._thread_lock=threading.RLock()
        self._file_lock=FileLock(f"{path}.lock", timeout=LOCK_TIMEOUT_SECONDS)
        self._state:dict[str, Any]|None=None
        self._signature:tuple[int, int]|None=None

    def exists(self)->bool:
        return self.path.exists()

    def _current_signature(self)->tuple[int, int]|None:
        try:
            stat=self.path.stat()
        except FileNotFoundError:
            return None

        return (stat.st_mtime_ns, stat.st_size)

    def _refresh(self)->dict[str, Any]:
        signature=self._current_signature()

        if self._state is not None and signature == self._signature:
            return self._state

        try:
            payload=read_json(self.path, default=None)
        except json.JSONDecodeError as error:
            # Never overwrite a damaged file.
            raise StoreCorruptedError(f"{self.path.name} is not valid JSON: {error}") from error

        state=empty_state()

        if isinstance(payload, dict):
            state.update(payload)

        self._state=state
        self._signature=signature

        return state

    def read(self, reader:Callable[[dict[str, Any]], Result])->Result:
        with self._thread_lock:
            return copy.deepcopy(reader(self._refresh()))

    def transact(self, mutator:Callable[[dict[str, Any]], Result])->Result:
        with self._thread_lock:
            try:
                with self._file_lock:
                    working=copy.deepcopy(self._refresh())
                    result=mutator(working)
                    atomic_write_json(self.path, working)
                    self._state=working
                    self._signature=self._current_signature()
            except Timeout as error:
                raise StoreBusyError("The data file is busy. Please try again.") from error

            return copy.deepcopy(result)

    def backup(self)->Path|None:
        if not self.path.exists():
            return None

        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target=self.path.parent/"backups"/f"{self.path.stem}-{stamp}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, target)

        return target
