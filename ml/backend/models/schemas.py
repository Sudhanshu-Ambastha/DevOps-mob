from pydantic import BaseModel
from typing import Optional, List

class ProblemCreate(BaseModel):
    title: str
    description: str
    is_paid: bool = False
    offered_budget: Optional[float] = 0.0
    tags: List[str] = []