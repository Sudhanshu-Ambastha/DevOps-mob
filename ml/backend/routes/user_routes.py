from fastapi import APIRouter, Request, Response

from ..controllers import user_controller
from ..dependencies import RepositoryDep, RequiredActorDep, SettingsDep
from ..models.schemas import LoginRequest, UserCreate, UserUpdate
from ..services.serializers import private_user

router=APIRouter(prefix="/api", tags=["Accounts"])


@router.post("/auth/register", status_code=201)
async def register(payload:UserCreate, request:Request, repository:RepositoryDep, settings:SettingsDep):
    return await user_controller.register_user(payload, repository, settings, request.app.state.auth_secret)


@router.post("/auth/login")
async def login(payload:LoginRequest, request:Request, repository:RepositoryDep, settings:SettingsDep):
    return await user_controller.login(payload, repository, settings, request.app.state.auth_secret)


@router.post("/auth/logout", status_code=204)
async def logout():
    return Response(status_code=204)


@router.get("/auth/me")
async def me(actor:RequiredActorDep):
    return private_user(actor)


@router.get("/auth/demo-accounts")
async def demo_accounts(repository:RepositoryDep, settings:SettingsDep):
    return await user_controller.list_demo_accounts(repository, settings)


@router.patch("/users/{user_id}")
async def update_profile(user_id:str, payload:UserUpdate, repository:RepositoryDep, actor:RequiredActorDep):
    return await user_controller.update_profile(user_id, payload, actor, repository)


@router.get("/workspace")
async def workspace(repository:RepositoryDep, actor:RequiredActorDep):
    return await user_controller.get_workspace(actor, repository)
