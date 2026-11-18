from typing import Any

from nlp.json_files import read_json

from ..auth import hash_password
from ..config.settings import Settings
from ..controllers.user_controller import DEMO_ACCOUNT_IDS
from ..repositories.base import Repository

Record=dict[str, Any]

MERGED_COLLECTIONS=("users", "problems", "community_reports", "relationships", "comments", "solutions", "upvotes")


def load_seed_dataset(settings:Settings)->Record:
    dataset=read_json(settings.dataset_path, default={}) or {}
    extra=read_json(settings.demo_problems_path, default=None)

    if not extra:
        return dataset

    merged=dict(dataset)

    for name in MERGED_COLLECTIONS:
        merged[name]=[*dataset.get(name, []), *extra.get(name, [])]

    return merged


async def ensure_demo_accounts(repository:Repository, settings:Settings)->list[str]:
    if settings.is_production:
        raise RuntimeError("Demo accounts are never created when APP_ENV is production.")

    prepared=[]

    for user_id in DEMO_ACCOUNT_IDS:
        user=await repository.get_user(user_id)

        if user is None:
            continue

        # A password someone already set is kept.
        if not user.get("password_hash"):
            await repository.update_user(user_id, {"password_hash":hash_password(settings.demo_account_password)})

        prepared.append(user["email"])

    return prepared
