from typing import Annotated, Literal

from fastapi import APIRouter, Query

from ..controllers import problem_controller, srs_controller
from ..dependencies import ActorDep, RepositoryDep, RequiredActorDep, SettingsDep, SrsGeneratorDep
from ..models.schemas import CommentCreate, SolutionCreate, SrsGenerateRequest, SrsUpdateRequest
from ..repositories.base import ProblemQuery

router = APIRouter(prefix="/api/problems", tags=["Problems"])

SortOption = Literal["trending", "newest", "most_upvoted", "most_reported", "most_solutions"]


@router.get("")
async def list_problems(
    repository: RepositoryDep,
    actor: ActorDep,
    search: str = "",
    category: str = "",
    status: str = "",
    tag: str = "",
    sort: SortOption = "trending",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24
):
    query = ProblemQuery(search, category, status, tag, sort, page, page_size)
    return await problem_controller.list_problems(query, actor, repository)


@router.get("/{problem_id}")
async def get_problem(problem_id: str, repository: RepositoryDep, actor: ActorDep):
    return await problem_controller.get_problem_detail(problem_id, actor, repository)


@router.post("/{problem_id}/upvote")
async def toggle_upvote(problem_id: str, repository: RepositoryDep, actor: RequiredActorDep):
    return await problem_controller.toggle_upvote(problem_id, actor, repository)


@router.post("/{problem_id}/follow")
async def toggle_follow(problem_id: str, repository: RepositoryDep, actor: RequiredActorDep):
    return await problem_controller.toggle_follow(problem_id, actor, repository)


@router.post("/{problem_id}/comments", status_code=201)
async def add_comment(
    problem_id: str,
    payload: CommentCreate,
    repository: RepositoryDep,
    actor: RequiredActorDep
):
    return await problem_controller.add_comment(problem_id, payload, actor, repository)


@router.post("/{problem_id}/solutions", status_code=201)
async def add_solution(
    problem_id: str,
    payload: SolutionCreate,
    repository: RepositoryDep,
    actor: RequiredActorDep
):
    return await problem_controller.add_solution(problem_id, payload, actor, repository)


@router.get("/{problem_id}/srs")
async def get_srs(problem_id: str, repository: RepositoryDep, version: int | None = None):
    return await srs_controller.get_srs(problem_id, version, repository)


@router.post("/{problem_id}/srs", status_code=201)
async def generate_srs(
    problem_id: str,
    payload: SrsGenerateRequest,
    repository: RepositoryDep,
    actor: ActorDep,
    generator: SrsGeneratorDep,
    settings: SettingsDep
):
    """
    Triggers automatic ISO/IEC/IEEE 29148 SRS generation via OpenRouter, 
    with built-in reuse logic for Community Reports and local path fallback handling.
    """
    return await srs_controller.generate_srs(
        problem_id, payload, actor, repository, generator, settings
    )


@router.put("/{problem_id}/srs/{version}")
async def update_srs(
    problem_id: str,
    version: int,
    payload: SrsUpdateRequest,
    repository: RepositoryDep,
    actor: RequiredActorDep
):
    return await srs_controller.update_srs(problem_id, version, payload, repository)