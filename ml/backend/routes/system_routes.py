from fastapi import APIRouter, Request

from ..controllers import problem_controller, system_controller
from ..dependencies import RepositoryDep, SettingsDep
from ..services.dashboard_service import build_dashboard

router=APIRouter(prefix="/api", tags=["System"])


@router.get("/health")
async def health(settings:SettingsDep):
    return {"status":"ok","storage":"mongodb" if settings.uses_mongodb else "json","database_required":settings.uses_mongodb}


@router.get("/meta")
async def meta():
    return system_controller.get_meta()


@router.get("/ai/status")
async def ai_status(request:Request, settings:SettingsDep):
    state=request.app.state

    return system_controller.get_ai_status(settings, state.embedding_provider, state.text_provider, state.usage_guard)


@router.get("/dashboard")
async def dashboard(repository:RepositoryDep):
    return build_dashboard(await repository.dashboard_snapshot())


@router.get("/solutions")
async def list_solutions(repository:RepositoryDep):
    return await problem_controller.list_solutions(repository)


@router.get("/solutions/{solution_id}")
async def get_solution(solution_id:str, repository:RepositoryDep):
    return await problem_controller.get_solution(solution_id, repository)
