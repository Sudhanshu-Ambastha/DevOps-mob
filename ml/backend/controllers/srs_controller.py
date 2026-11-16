from typing import Any

from nlp.errors import ProviderDisabled
from nlp.srs import SrsContext, SrsGenerator

from ..config.settings import Settings
from ..errors import AppError, consent_required, not_found
from ..models.schemas import SrsGenerateRequest, SrsUpdateRequest
from ..repositories.base import Repository
from ..services.serializers import srs_view
from ..utils import utc_now_iso
from .problem_controller import require_problem

Record=dict[str, Any]

MAX_REPORTS_IN_PROMPT=5
MAX_REPORT_CHARS=800

# Prevent duplicate generation requests.
_generating:set[str]=set()


def _versions_summary(documents:list[Record])->list[Record]:
    return [
        {"version":item["version"],"status":item["status"],"updated_at":item["updated_at"]}
        for item in documents
    ]


async def get_srs(problem_id:str, version:int|None, repository:Repository)->Record:
    await require_problem(problem_id, repository)
    documents=await repository.list_srs_versions(problem_id)

    if not documents:
        return {"document":None,"versions":[]}

    selected=documents[-1]

    if version is not None:
        selected=next((item for item in documents if item["version"] == version), None)

        if selected is None:
            raise not_found("This SRS version")

    return {"document":srs_view(selected),"versions":_versions_summary(documents)}


async def _build_context(problem:Record, repository:Repository)->SrsContext:
    reports=await repository.list_reports(problem["id"])
    allowed=[report for report in reports if report.get("ai_processing_allowed", False)]
    texts=[report["description"][:MAX_REPORT_CHARS] for report in allowed[:MAX_REPORTS_IN_PROMPT]]

    return SrsContext(
        title=problem["title"],
        description=problem["description"],
        category=problem.get("category", ""),
        tags=problem.get("tags", []),
        outcome=problem.get("outcome", ""),
        constraints=problem.get("constraints", ""),
        community_reports=texts
    )


async def generate_srs(
    problem_id:str,
    payload:SrsGenerateRequest,
    actor:Record|None,
    repository:Repository,
    generator:SrsGenerator,
    settings:Settings
)->Record:
    if not settings.ai_enabled:
        raise ProviderDisabled("AI generation is turned off for this server.", provider="openrouter")

    if not payload.ai_consent:
        raise consent_required()

    problem=await require_problem(problem_id, repository)
    is_author=actor is not None and actor["id"] == problem.get("author_id")

    if not problem.get("ai_processing_allowed", False) and not is_author:
        raise AppError(403, "ai_not_permitted", "The author of this problem did not allow AI processing.")

    if problem_id in _generating:
        raise AppError(409, "srs_in_progress", "An SRS is already being generated for this problem.")

    _generating.add(problem_id)

    try:
        draft=await generator.generate(await _build_context(problem, repository))
    finally:
        _generating.discard(problem_id)

    timestamp=utc_now_iso()

    await repository.save_srs({
        "problem_id":problem_id,
        "markdown":draft.markdown,
        "status":"ai_draft",
        "model":draft.model,
        "is_complete":draft.is_complete,
        "warnings":draft.warnings,
        "generated_at":timestamp,
        "updated_at":timestamp
    })

    return await get_srs(problem_id, None, repository)


async def update_srs(problem_id:str, version:int, payload:SrsUpdateRequest, repository:Repository)->Record:
    await require_problem(problem_id, repository)
    status="reviewed" if payload.mark_reviewed else "edited"
    changes={"markdown":payload.markdown,"status":status,"updated_at":utc_now_iso()}
    document=await repository.update_srs(problem_id, version, changes)

    if document is None:
        raise not_found("This SRS version")

    return await get_srs(problem_id, version, repository)
