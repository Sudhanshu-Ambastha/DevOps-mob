from typing import Any

from ..auth import create_token, hash_password, verify_password
from ..config.settings import Settings
from ..errors import AppError, not_found
from ..models.schemas import LoginRequest, UserCreate, UserUpdate
from ..repositories.base import Repository
from ..services.serializers import private_user, problem_summary, solution_view, users_index
from ..utils import new_id, utc_now_iso

Record=dict[str, Any]

DEMO_ACCOUNT_IDS=("syn-user-01", "syn-user-02", "syn-user-03")

# Keeps the response time similar whether or not the email exists.
_UNKNOWN_USER_HASH=hash_password("unknown-user-placeholder")


def _session(user:Record, settings:Settings, secret:str)->Record:
    token=create_token(user["id"], secret, settings.auth_token_hours)

    return {"user":private_user(user),"token":token,"expires_in_hours":settings.auth_token_hours}


async def register_user(payload:UserCreate, repository:Repository, settings:Settings, secret:str)->Record:
    email=payload.email.strip().lower()

    if await repository.find_user_by_email(email) is not None:
        raise AppError(409, "email_in_use", "An account already uses this email address.")

    user=await repository.create_user({
        "id":new_id("user"),
        "name":payload.name.strip(),
        "email":email,
        "password_hash":hash_password(payload.password),
        "role":payload.role,
        "bio":"",
        "skills":[],
        "source":"runtime",
        "created_at":utc_now_iso()
    })

    return _session(user, settings, secret)


async def login(payload:LoginRequest, repository:Repository, settings:Settings, secret:str)->Record:
    user=await repository.find_user_by_email(payload.email.strip().lower())
    stored=user.get("password_hash") if user else _UNKNOWN_USER_HASH

    if not verify_password(payload.password, stored) or user is None:
        raise AppError(401, "invalid_credentials", "The email or password is incorrect.")

    return _session(user, settings, secret)


async def list_demo_accounts(repository:Repository, settings:Settings)->list[Record]:
    if settings.is_production:
        return []

    accounts=[]

    for user_id in DEMO_ACCOUNT_IDS:
        user=await repository.get_user(user_id)

        if user and user.get("password_hash"):
            accounts.append({"name":user["name"],"email":user["email"],"role":user.get("role", "user")})

    return accounts


async def update_profile(user_id:str, payload:UserUpdate, actor:Record, repository:Repository)->Record:
    if actor["id"] != user_id:
        raise AppError(403, "not_your_profile", "You can only edit your own profile.")

    changes={
        "name":payload.name.strip(),
        "bio":payload.bio.strip(),
        "skills":[skill.strip() for skill in payload.skills if skill.strip()],
        "role":payload.role
    }
    user=await repository.update_user(user_id, changes)

    if user is None:
        raise not_found("This profile")

    return private_user(user)


async def get_workspace(actor:Record, repository:Repository)->Record:
    user_id=actor["id"]
    problems=await repository.list_all_problems()
    users=users_index(await repository.list_users())
    upvoted=await repository.upvoted_problem_ids(user_id)
    followed=await repository.followed_problem_ids(user_id)
    by_id={problem["id"]:problem for problem in problems}
    solutions=[item for item in await repository.list_solutions() if item.get("author_id") == user_id]

    def summaries(selected:list[Record])->list[Record]:
        return [problem_summary(problem, users, upvoted, followed) for problem in selected]

    return {
        "problems":summaries([problem for problem in problems if problem.get("author_id") == user_id]),
        "supported":summaries([problem for problem in problems if problem["id"] in upvoted]),
        "followed":summaries([problem for problem in problems if problem["id"] in followed]),
        "solutions":[solution_view(item, users, by_id.get(item["problem_id"])) for item in solutions]
    }

