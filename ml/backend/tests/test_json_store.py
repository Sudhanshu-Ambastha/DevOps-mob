import json
import threading
from pathlib import Path

import pytest

from backend.repositories.json_store import JsonStore, StoreCorruptedError
from nlp.json_files import atomic_write_json


def add_user(state:dict)->int:
    state["users"].append({"id":str(len(state["users"]))})

    return len(state["users"])


def test_saves_and_reloads_from_disk(tmp_path:Path):
    path=tmp_path/"store.json"
    JsonStore(path).transact(add_user)

    assert JsonStore(path).read(lambda state:len(state["users"])) == 1


def test_failed_change_leaves_stored_data_untouched(tmp_path:Path):
    path=tmp_path/"store.json"
    store=JsonStore(path)
    store.transact(add_user)

    def fails_halfway(state:dict)->None:
        state["users"].append({"id":"half-written"})
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        store.transact(fails_halfway)

    assert store.read(lambda state:len(state["users"])) == 1
    assert len(json.loads(path.read_text(encoding="utf-8"))["users"]) == 1


def test_atomic_write_keeps_old_file_if_serialising_fails(tmp_path:Path):
    path=tmp_path/"data.json"
    atomic_write_json(path, {"safe":True})

    with pytest.raises(TypeError):
        atomic_write_json(path, {"bad":object()})

    assert json.loads(path.read_text(encoding="utf-8")) == {"safe":True}
    assert [item.name for item in tmp_path.iterdir()] == ["data.json"]


def test_corrupted_file_is_reported_and_never_overwritten(tmp_path:Path):
    path=tmp_path/"store.json"
    path.write_text("{ this is not json", encoding="utf-8")
    store=JsonStore(path)

    with pytest.raises(StoreCorruptedError):
        store.transact(add_user)

    assert path.read_text(encoding="utf-8") == "{ this is not json"


def test_readers_cannot_change_stored_state_by_accident(tmp_path:Path):
    store=JsonStore(tmp_path/"store.json")
    store.transact(add_user)
    users=store.read(lambda state:state["users"])
    users.clear()

    assert store.read(lambda state:len(state["users"])) == 1


def test_parallel_writers_from_separate_stores_lose_nothing(tmp_path:Path):
    path=tmp_path/"store.json"
    per_thread=15

    def worker()->None:
        store=JsonStore(path)

        for _ in range(per_thread):
            store.transact(add_user)

    threads=[threading.Thread(target=worker) for _ in range(4)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert JsonStore(path).read(lambda state:len(state["users"])) == 4*per_thread


def test_a_second_store_sees_changes_from_the_first(tmp_path:Path):
    path=tmp_path/"store.json"
    first=JsonStore(path)
    second=JsonStore(path)
    first.transact(add_user)
    assert second.read(lambda state:len(state["users"])) == 1

    first.transact(add_user)
    assert second.read(lambda state:len(state["users"])) == 2
