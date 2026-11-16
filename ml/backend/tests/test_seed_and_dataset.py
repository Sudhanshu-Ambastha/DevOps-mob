import asyncio
import json

import pytest

from backend.config.settings import ML_ROOT
from backend.repositories.json_repository import JsonRepository
from backend.scripts.seed import run as run_seed_command
from nlp.json_files import read_json
from nlp.training_data import LABELS, build_training_rows

from .conftest import MEMBER, draft


@pytest.fixture
def dataset()->dict:
    return read_json(ML_ROOT/"data"/"synthetic_dataset.json")


def test_dataset_references_are_all_valid(dataset:dict):
    users={user["id"] for user in dataset["users"]}
    problems={problem["id"] for problem in dataset["problems"]}

    for problem in dataset["problems"]:
        assert problem["author_id"] in users

    for name in ("community_reports", "comments", "solutions"):
        for record in dataset[name]:
            assert record["problem_id"] in problems
            assert record["author_id"] in users

    for upvote in dataset["upvotes"]:
        assert upvote["problem_id"] in problems
        assert upvote["user_id"] in users

    for link in dataset["relationships"]:
        assert link["source_problem_id"] in problems
        assert link["target_problem_id"] in problems
        assert link["source_problem_id"] != link["target_problem_id"]


def test_dataset_covers_required_categories_and_labels(dataset:dict):
    categories={problem["category"] for problem in dataset["problems"]}
    required={
        "Expense management","Education","Healthcare","Transportation",
        "Small business","Productivity","Environment","Community services"
    }

    assert required <= categories
    assert {pair["label"] for pair in dataset["labelled_pairs"]} == set(LABELS)


def test_dataset_upvotes_are_unique_and_never_self_votes(dataset:dict):
    authors={problem["id"]:problem["author_id"] for problem in dataset["problems"]}
    pairs=[(item["problem_id"], item["user_id"]) for item in dataset["upvotes"]]

    assert len(pairs) == len(set(pairs))
    assert all(authors[problem_id] != user_id for problem_id, user_id in pairs)


def test_repeated_seeding_adds_nothing(tmp_path, dataset:dict):
    repository=JsonRepository(tmp_path/"store.json")
    first=asyncio.run(repository.seed(dataset))
    second=asyncio.run(repository.seed(dataset))
    problems=asyncio.run(repository.list_all_problems())

    assert first["added"]["problems"] == len(dataset["problems"])
    assert second["added"] == {}
    assert len(problems) == len(dataset["problems"])
    assert len({problem["id"] for problem in problems}) == len(problems)


def test_seed_keeps_counts_consistent_with_records(tmp_path, dataset:dict):
    repository=JsonRepository(tmp_path/"store.json")
    asyncio.run(repository.seed(dataset))
    snapshot=asyncio.run(repository.dashboard_snapshot())

    assert sum(item["upvote_count"] for item in snapshot["problems"]) == len(dataset["upvotes"])
    assert sum(item["report_count"] for item in snapshot["problems"]) == len(dataset["community_reports"])


def test_normal_seed_never_touches_runtime_submissions(client, settings, dataset:dict):
    session=client.post("/api/submissions/analyze", json=draft(title="A brand new runtime problem here"), headers=MEMBER).json()
    created=client.post(f"/api/submissions/{session['session_id']}/decision", json={"decision":"none"}, headers=MEMBER).json()

    repository=JsonRepository(settings.runtime_store_path)
    asyncio.run(repository.seed(dataset))

    saved=asyncio.run(repository.get_problem(created["problem_id"]))
    assert saved["title"] == "A brand new runtime problem here"
    assert saved["source"] == "runtime"


def test_reset_makes_a_backup_first(client, settings, dataset:dict):
    session=client.post("/api/submissions/analyze", json=draft(), headers=MEMBER).json()
    client.post(f"/api/submissions/{session['session_id']}/decision", json={"decision":"none"}, headers=MEMBER)

    repository=JsonRepository(settings.runtime_store_path)
    summary=asyncio.run(repository.reset(dataset))
    problems=asyncio.run(repository.list_all_problems())

    assert len(problems) == len(dataset["problems"])

    with open(summary["backup"], encoding="utf-8") as file:
        backup=json.load(file)

    assert len(backup["problems"]) == len(dataset["problems"])+1


def test_reset_command_refuses_without_confirmation(monkeypatch, settings):
    monkeypatch.setattr("backend.scripts.seed.get_settings", lambda:settings)

    class Arguments:
        reset=True
        yes=False

    assert asyncio.run(run_seed_command(Arguments())) == 1
    assert not settings.runtime_store_path.exists()


def test_training_rows_use_only_real_labels(dataset:dict):
    feedback=[
        {"id":"a","label":"same_underlying","label_source":"user_explicit","features":{}},
        {"id":"b","label":None,"label_source":"shown_not_selected","features":{}}
    ]
    export=build_training_rows(dataset, feedback)

    assert export["row_count"] == len(dataset["labelled_pairs"])+1
    assert all(row["label"] in LABELS for row in export["rows"])
    assert export["rows"][0]["source"] == "synthetic"
