from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

Record=dict[str, Any]


@dataclass
class ProblemQuery:
    search:str=""
    category:str=""
    status:str=""
    tag:str=""
    sort:str="trending"
    page:int=1
    page_size:int=24


@dataclass
class DecisionPlan:
    result:Record
    fingerprint:str
    problem:Record|None=None
    report:Record|None=None
    relationship:Record|None=None
    feedback:list[Record]=field(default_factory=list)


class Repository(ABC):
    @abstractmethod
    async def list_users(self)->list[Record]:
        pass

    @abstractmethod
    async def get_user(self, user_id:str)->Record|None:
        pass

    @abstractmethod
    async def create_user(self, user:Record)->Record:
        pass

    @abstractmethod
    async def update_user(self, user_id:str, changes:Record)->Record|None:
        pass

    @abstractmethod
    async def find_problems(self, query:ProblemQuery)->tuple[list[Record], int]:
        pass

    @abstractmethod
    async def list_all_problems(self)->list[Record]:
        pass

    @abstractmethod
    async def get_problem(self, problem_id:str)->Record|None:
        pass

    @abstractmethod
    async def get_problems(self, problem_ids:list[str])->list[Record]:
        pass

    @abstractmethod
    async def toggle_upvote(self, problem_id:str, user_id:str)->tuple[bool, int]:
        pass

    @abstractmethod
    async def toggle_follow(self, problem_id:str, user_id:str)->bool:
        pass

    @abstractmethod
    async def upvoted_problem_ids(self, user_id:str)->set[str]:
        pass

    @abstractmethod
    async def followed_problem_ids(self, user_id:str)->set[str]:
        pass

    @abstractmethod
    async def list_reports(self, problem_id:str)->list[Record]:
        pass

    @abstractmethod
    async def list_relationships(self, problem_id:str)->list[Record]:
        pass

    @abstractmethod
    async def list_comments(self, problem_id:str)->list[Record]:
        pass

    @abstractmethod
    async def add_comment(self, comment:Record)->Record:
        pass

    @abstractmethod
    async def list_solutions(self, problem_id:str|None=None)->list[Record]:
        pass

    @abstractmethod
    async def get_solution(self, solution_id:str)->Record|None:
        pass

    @abstractmethod
    async def add_solution(self, solution:Record)->Record:
        pass

    @abstractmethod
    async def create_match_session(self, session:Record, ttl_hours:int)->Record:
        pass

    @abstractmethod
    async def get_match_session(self, session_id:str)->Record|None:
        pass

    @abstractmethod
    async def find_open_session_by_request(self, client_request_id:str)->Record|None:
        pass

    @abstractmethod
    async def commit_decision(self, session_id:str, plan:DecisionPlan)->Record:
        pass

    @abstractmethod
    async def list_feedback(self)->list[Record]:
        pass

    @abstractmethod
    async def list_srs_versions(self, problem_id:str)->list[Record]:
        pass

    @abstractmethod
    async def save_srs(self, document:Record)->Record:
        pass

    @abstractmethod
    async def update_srs(self, problem_id:str, version:int, changes:Record)->Record|None:
        pass

    @abstractmethod
    async def dashboard_snapshot(self)->Record:
        pass

    @abstractmethod
    async def seed(self, dataset:Record)->Record:
        pass

    @abstractmethod
    async def reset(self, dataset:Record)->Record:
        pass
