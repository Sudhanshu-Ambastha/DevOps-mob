from motor.motor_asyncio import AsyncIOMotorDatabase
from models.schemas import ProblemCreate
from services.ai_service import analyze_problem_text, create_srs_spec

async def handle_create_problem(problem: ProblemCreate, db: AsyncIOMotorDatabase):
    # 1. Check for semantic duplicates against existing problems
    cursor = db.problems.find({})
    existing_problems = await cursor.to_list(length=100)
    
    for existing in existing_problems:
        score = analyze_problem_text(existing["description"], problem.description)
        if score >= 0.82:  # Duplicate threshold
            await db.problems.update_one(
                {"_id": existing["_id"]},
                {"$inc": {"upvotes": 1}}
            )
            return {
                "message": "Similar problem detected! Upvoted the existing issue instead.",
                "is_duplicate": True,
                "redirect_id": str(existing["_id"])
            }

    # 2. Generate local SRS and Tech Stack recommendation
    srs_text = create_srs_spec(problem.description)
    budget_str = f"₹{problem.offered_budget}" if problem.is_paid else "Unpaid / Open Source Contribution"

    # 3. Insert into MongoDB
    new_doc = {
        "title": problem.title,
        "description": problem.description,
        "srs_specification": srs_text,
        "is_paid": problem.is_paid,
        "offered_budget": problem.offered_budget,
        "budget_range": budget_str,
        "upvotes": 1,
        "tags": problem.tags
    }
    
    result = await db.problems.insert_one(new_doc)
    new_doc["id"] = str(result.inserted_id)
    del new_doc["_id"]

    return {
        "message": "Problem successfully posted and analyzed by AI Core.",
        "is_duplicate": False,
        "data": new_doc
    }

async def handle_get_problems(db: AsyncIOMotorDatabase):
    cursor = db.problems.find({})
    problems = await cursor.to_list(length=100)
    for p in problems:
        p["id"] = str(p["_id"])
        del p["_id"]
    return problems