from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from config.database import get_db
from models.schemas import ProblemCreate
from controllers.problem_controller import handle_create_problem, handle_get_problems

router = APIRouter(prefix="/api/problems", tags=["Problems"])

@router.post("")
async def create_problem_route(problem: ProblemCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await handle_create_problem(problem, db)

@router.get("")
async def get_problems_route(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await handle_get_problems(db)