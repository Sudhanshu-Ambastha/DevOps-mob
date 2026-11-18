from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CATEGORIES=[
    "Expense management",
    "Education",
    "Healthcare",
    "Transportation",
    "Small business",
    "Productivity",
    "Environment",
    "Community services",
    "Campus life",
    "Software development",
    "Web applications",
    "Mobile applications",
    "Networking",
    "Security",
    "Accessibility",
    "Hardware and IoT",
    "Other"
]

STATUSES=["open","in-progress","solved"]
SORT_OPTIONS=["trending","newest","most_upvoted","most_reported","most_solutions"]
MAX_TAGS=8


class SubmissionDraft(BaseModel):
    title:str=Field(min_length=12, max_length=160)
    description:str=Field(min_length=40, max_length=5000)
    category:str="Other"
    tags:list[str]=Field(default_factory=list)
    outcome:str=Field(min_length=12, max_length=1500)
    constraints:str=Field(default="", max_length=1500)
    is_paid:bool=False
    budget_range:str=Field(default="", max_length=80)

    @field_validator("title", "description", "outcome", "constraints", "budget_range", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("category")
    @classmethod
    def known_category(cls, value:str)->str:
        if value not in CATEGORIES:
            raise ValueError("Choose one of the listed categories.")

        return value

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value:list[str])->list[str]:
        tags=[]

        for tag in value:
            cleaned=tag.strip().lower()

            if cleaned and cleaned not in tags:
                tags.append(cleaned[:32])

        return tags[:MAX_TAGS]

    @model_validator(mode="after")
    def budget_only_when_paid(self):
        if not self.is_paid:
            self.budget_range=""
        elif not self.budget_range:
            self.budget_range="To be discussed"

        return self


class AnalyzeRequest(SubmissionDraft):
    ai_consent:bool=False
    client_request_id:str|None=Field(default=None, max_length=64)


class DecisionRequest(BaseModel):
    decision:Literal["same","related","none"]
    target_problem_id:str|None=None

    @model_validator(mode="after")
    def target_matches_decision(self):
        if self.decision in ("same", "related") and not self.target_problem_id:
            raise ValueError("Choose which suggested problem this decision applies to.")

        if self.decision == "none":
            self.target_problem_id=None

        return self


class CommentCreate(BaseModel):
    text:str=Field(min_length=1, max_length=2000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class SolutionCreate(BaseModel):
    title:str=Field(min_length=5, max_length=120)
    description:str=Field(min_length=20, max_length=3000)
    repo_url:str=Field(default="", max_length=300)
    tech_stack:list[str]=Field(default_factory=list)

    @field_validator("title", "description", "repo_url", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("repo_url")
    @classmethod
    def http_link(cls, value:str)->str:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("Repository link should start with http:// or https://")

        return value


class UserCreate(BaseModel):
    name:str=Field(min_length=2, max_length=80)
    email:str=Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=160)
    password:str=Field(min_length=8, max_length=128)
    role:Literal["user","developer"]="user"


class LoginRequest(BaseModel):
    email:str=Field(min_length=3, max_length=160)
    password:str=Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    name:str=Field(min_length=2, max_length=80)
    bio:str=Field(default="", max_length=500)
    skills:list[str]=Field(default_factory=list)
    role:Literal["user","developer"]="user"


class SrsGenerateRequest(BaseModel):
    ai_consent:bool=False


class SrsUpdateRequest(BaseModel):
    markdown:str=Field(min_length=1, max_length=60000)
    mark_reviewed:bool=False
