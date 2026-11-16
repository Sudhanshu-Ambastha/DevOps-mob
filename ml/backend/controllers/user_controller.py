from typing import Any

from ..errors import AppError, not_found
from ..models.schemas import UserCreate, UserUpdate
from ..repositories.base import Repository
from ..services.serializers import problem_summary, public_user, solution_view, users_index
from ..utils import new_id, utc_now_iso

Record=dict[str, Any]


async def list_demo_profiles(repository:Repository)->list[Record]:
    users=await repository.list_users()

    return [public_user(user) for user in users if user.get("demo_profile")]


async def start_demo_session(user_id:str, repository:Repository)->Record:
    user=await repository.get_user(user_id)

    if user is None:
        raise not_found("This demo profile")

    return public_user(user)


async def register_demo_user(payload:UserCreate, repository:Repository)->Record:
    email=payload.email.strip().lower()
    users=await repository.list_users()

    if any(user.get("email") == email for user in users):
        raise AppError(409, "email_in_use", "A demo profile already uses this email address.")

    user=await repository.create_user({
        "id":new_id("user"),
        "name":payload.name.strip(),
        "email":email,
        "role":payload.role,
        "bio":"",
        "skills":[],
        "source":"runtime",
        "created_at":utc_now_iso()
    })

    return public_user(user)


async def update_profile(user_id:str, payload:UserUpdate, actor:Record, repository:Repository)->Record:
    if actor["id"] != user_id:
        raise AppError(403, "not_your_profile", "You can only edit your own demo profile.")

    changes={
        "name":payload.name.strip(),
        "bio":payload.bio.strip(),
        "skills":[skill.strip() for skill in payload.skills if skill.strip()],
        "role":payload.role
    }
    user=await repository.update_user(user_id, changes)

    if user is None:
        raise not_found("This demo profile")

    return public_user(user)


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
