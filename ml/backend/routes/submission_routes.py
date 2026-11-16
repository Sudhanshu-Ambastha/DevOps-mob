from fastapi import APIRouter

from ..controllers import submission_controller
from ..dependencies import ActorDep, MatcherDep, RepositoryDep, SettingsDep
from ..models.schemas import AnalyzeRequest, DecisionRequest

router=APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.post("/analyze")
async def analyze(
    payload:AnalyzeRequest,
    repository:RepositoryDep,
    actor:ActorDep,
    matcher:MatcherDep,
    settings:SettingsDep
):
    return await submission_controller.analyze_submission(payload, actor, repository, matcher, settings)


@router.post("/{session_id}/decision")
async def decide(
    session_id:str,
    payload:DecisionRequest,
    repository:RepositoryDep,
    actor:ActorDep,
    settings:SettingsDep
):
    return await submission_controller.decide_submission(session_id, payload, actor, repository, settings)
