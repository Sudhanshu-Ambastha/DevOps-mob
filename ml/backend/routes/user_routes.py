from fastapi import APIRouter

from ..controllers import user_controller
from ..dependencies import RepositoryDep, RequiredActorDep
from ..models.schemas import DemoSessionRequest, UserCreate, UserUpdate

router=APIRouter(prefix="/api", tags=["Demo profiles"])


@router.get("/demo-profiles")
async def list_demo_profiles(repository:RepositoryDep):
    return await user_controller.list_demo_profiles(repository)


@router.post("/demo-session")
async def start_demo_session(payload:DemoSessionRequest, repository:RepositoryDep):
    return await user_controller.start_demo_session(payload.user_id, repository)


@router.post("/users", status_code=201)
async def register(payload:UserCreate, repository:RepositoryDep):
    return await user_controller.register_demo_user(payload, repository)


@router.patch("/users/{user_id}")
async def update_profile(user_id:str, payload:UserUpdate, repository:RepositoryDep, actor:RequiredActorDep):
    return await user_controller.update_profile(user_id, payload, actor, repository)


@router.get("/workspace")
async def workspace(repository:RepositoryDep, actor:RequiredActorDep):
    return await user_controller.get_workspace(actor, repository)
