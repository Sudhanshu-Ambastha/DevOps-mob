import asyncio
from collections import Counter
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable

from ..utils import parse_time, recent_upvote_counts, utc_now
from .base import DecisionPlan, ProblemQuery, Record, Repository
from .json_store import COLLECTIONS, JsonStore, empty_state

SEEDED_COLLECTIONS=("users", "problems", "community_reports", "relationships", "comments", "solutions")


class RecordNotFound(Exception):
    pass


def find_by_id(records:list[Record], record_id:str)->Record|None:
    return next((record for record in records if record.get("id") == record_id), None)


def refresh_counts(state:Record, problem:Record)->None:
    problem_id=problem["id"]
    problem["upvote_count"]=sum(1 for item in state["upvotes"] if item["problem_id"] == problem_id)
    problem["report_count"]=sum(1 for item in state["community_reports"] if item["problem_id"] == problem_id)
    problem["comment_count"]=sum(1 for item in state["comments"] if item["problem_id"] == problem_id)
    problem["solution_count"]=sum(1 for item in state["solutions"] if item["problem_id"] == problem_id)


class JsonRepository(Repository):
    def __init__(self, path:Path):
        self.store=JsonStore(path)

    async def _read(self, reader:Callable[[Record], Any])->Any:
        return await asyncio.to_thread(self.store.read, reader)

    async def _write(self, mutator:Callable[[Record], Any])->Any:
        return await asyncio.to_thread(self.store.transact, mutator)

    async def list_users(self)->list[Record]:
        return await self._read(lambda state:state["users"])

    async def get_user(self, user_id:str)->Record|None:
        return await self._read(lambda state:find_by_id(state["users"], user_id))

    async def find_user_by_email(self, email:str)->Record|None:
        def reader(state:Record)->Record|None:
            return next((user for user in state["users"] if user.get("email") == email), None)

        return await self._read(reader)

    async def is_empty(self)->bool:
        return not self.store.exists()

    async def create_user(self, user:Record)->Record:
        def mutate(state:Record)->Record:
            state["users"].append(user)

            return user

        return await self._write(mutate)

    async def update_user(self, user_id:str, changes:Record)->Record|None:
        def mutate(state:Record)->Record|None:
            user=find_by_id(state["users"], user_id)

            if user is not None:
                user.update(changes)

            return user

        return await self._write(mutate)

    async def find_problems(self, query:ProblemQuery)->tuple[list[Record], int]:
        def reader(state:Record)->tuple[list[Record], int]:
            matches=[problem for problem in state["problems"] if self._matches(problem, query)]
            matches=self._sorted(matches, query.sort, state["upvotes"])
            start=(query.page-1)*query.page_size

            return (matches[start:start+query.page_size], len(matches))

        return await self._read(reader)

    def _matches(self, problem:Record, query:ProblemQuery)->bool:
        if query.category and problem["category"] != query.category:
            return False

        if query.status and problem["status"] != query.status:
            return False

        if query.tag and query.tag.lower() not in problem["tags"]:
            return False

        if not query.search.strip():
            return True

        searchable=f"{problem['title']} {problem['description']} {' '.join(problem['tags'])}".lower()

        return query.search.strip().lower() in searchable

    def _sorted(self, problems:list[Record], sort:str, upvotes:list[Record])->list[Record]:
        by_newest=sorted(problems, key=lambda problem:problem["created_at"], reverse=True)

        if sort == "newest":
            return by_newest

        if sort == "most_upvoted":
            return sorted(by_newest, key=lambda problem:problem["upvote_count"], reverse=True)

        if sort == "most_reported":
            return sorted(by_newest, key=lambda problem:problem["report_count"], reverse=True)

        if sort == "most_solutions":
            return sorted(by_newest, key=lambda problem:problem["solution_count"], reverse=True)

        recent=recent_upvote_counts(upvotes)

        return sorted(by_newest, key=lambda problem:recent[problem["id"]], reverse=True)

    async def list_all_problems(self)->list[Record]:
        return await self._read(lambda state:state["problems"])

    async def get_problem(self, problem_id:str)->Record|None:
        return await self._read(lambda state:find_by_id(state["problems"], problem_id))

    async def get_problems(self, problem_ids:list[str])->list[Record]:
        wanted=set(problem_ids)

        return await self._read(lambda state:[item for item in state["problems"] if item["id"] in wanted])

    async def toggle_upvote(self, problem_id:str, user_id:str)->tuple[bool, int]:
        def mutate(state:Record)->tuple[bool, int]:
            problem=self._require_problem(state, problem_id)
            active=self._toggle_link(state["upvotes"], problem_id, user_id)
            refresh_counts(state, problem)

            return (active, problem["upvote_count"])

        return await self._write(mutate)

    async def toggle_follow(self, problem_id:str, user_id:str)->bool:
        def mutate(state:Record)->bool:
            self._require_problem(state, problem_id)

            return self._toggle_link(state["follows"], problem_id, user_id)

        return await self._write(mutate)

    def _require_problem(self, state:Record, problem_id:str)->Record:
        problem=find_by_id(state["problems"], problem_id)

        if problem is None:
            raise RecordNotFound(problem_id)

        return problem

    def _toggle_link(self, links:list[Record], problem_id:str, user_id:str)->bool:
        for link in links:
            if link["problem_id"] == problem_id and link["user_id"] == user_id:
                links.remove(link)
                return False

        links.append({"problem_id":problem_id,"user_id":user_id,"created_at":utc_now().isoformat(),"source":"runtime"})

        return True

    async def upvoted_problem_ids(self, user_id:str)->set[str]:
        return await self._read(lambda state:{item["problem_id"] for item in state["upvotes"] if item["user_id"] == user_id})

    async def followed_problem_ids(self, user_id:str)->set[str]:
        return await self._read(lambda state:{item["problem_id"] for item in state["follows"] if item["user_id"] == user_id})

    async def list_reports(self, problem_id:str)->list[Record]:
        def reader(state:Record)->list[Record]:
            reports=[report for report in state["community_reports"] if report["problem_id"] == problem_id]

            return sorted(reports, key=lambda report:report["created_at"])

        return await self._read(reader)

    async def list_relationships(self, problem_id:str)->list[Record]:
        def reader(state:Record)->list[Record]:
            links=state["relationships"]

            return [link for link in links if problem_id in (link["source_problem_id"], link["target_problem_id"])]

        return await self._read(reader)

    async def list_comments(self, problem_id:str)->list[Record]:
        def reader(state:Record)->list[Record]:
            comments=[comment for comment in state["comments"] if comment["problem_id"] == problem_id]

            return sorted(comments, key=lambda comment:comment["created_at"])

        return await self._read(reader)

    async def add_comment(self, comment:Record)->Record:
        def mutate(state:Record)->Record:
            problem=self._require_problem(state, comment["problem_id"])
            state["comments"].append(comment)
            refresh_counts(state, problem)
            problem["updated_at"]=comment["created_at"]

            return comment

        return await self._write(mutate)

    async def list_solutions(self, problem_id:str|None=None)->list[Record]:
        def reader(state:Record)->list[Record]:
            solutions=state["solutions"]

            if problem_id is not None:
                solutions=[solution for solution in solutions if solution["problem_id"] == problem_id]

            return sorted(solutions, key=lambda solution:solution["created_at"], reverse=True)

        return await self._read(reader)

    async def get_solution(self, solution_id:str)->Record|None:
        return await self._read(lambda state:find_by_id(state["solutions"], solution_id))

    async def add_solution(self, solution:Record)->Record:
        def mutate(state:Record)->Record:
            problem=self._require_problem(state, solution["problem_id"])
            state["solutions"].append(solution)
            refresh_counts(state, problem)
            problem["updated_at"]=solution["created_at"]

            if problem["status"] == "open":
                problem["status"]="in-progress"

            return solution

        return await self._write(mutate)

    async def create_match_session(self, session:Record, ttl_hours:int)->Record:
        def mutate(state:Record)->Record:
            self._remove_expired_sessions(state, ttl_hours)
            state["match_sessions"].append(session)

            return session

        return await self._write(mutate)

    def _remove_expired_sessions(self, state:Record, ttl_hours:int)->None:
        cutoff=utc_now()-timedelta(hours=ttl_hours)
        kept=[]

        for session in state["match_sessions"]:
            if session["status"] != "open" or parse_time(session["created_at"]) >= cutoff:
                kept.append(session)

        state["match_sessions"]=kept

    async def get_match_session(self, session_id:str)->Record|None:
        return await self._read(lambda state:find_by_id(state["match_sessions"], session_id))

    async def find_open_session_by_request(self, client_request_id:str)->Record|None:
        def reader(state:Record)->Record|None:
            for session in state["match_sessions"]:
                if session["status"] == "open" and session.get("client_request_id") == client_request_id:
                    return session

            return None

        return await self._read(reader)

    async def commit_decision(self, session_id:str, plan:DecisionPlan)->Record:
        def mutate(state:Record)->Record:
            session=find_by_id(state["match_sessions"], session_id)

            if session is None:
                raise RecordNotFound(session_id)

            if session["status"] == "decided":
                return {**session["result"],"replayed":True}

            existing=self._find_existing_submission(state, plan.fingerprint)

            if existing is not None:
                return self._close_as_duplicate_submission(session, existing, plan)

            self._apply_plan(state, plan)
            self._close_session(session, plan.result)

            return plan.result

        return await self._write(mutate)

    def _find_existing_submission(self, state:Record, fingerprint:str)->Record|None:
        for problem in state["problems"]:
            if problem.get("fingerprint") == fingerprint:
                return {"problem_id":problem["id"],"report_id":None}

        for report in state["community_reports"]:
            if report.get("fingerprint") == fingerprint:
                return {"problem_id":report["problem_id"],"report_id":report["id"]}

        return None

    def _close_as_duplicate_submission(self, session:Record, existing:Record, plan:DecisionPlan)->Record:
        result={
            **plan.result,
            "problem_id":existing["problem_id"],
            "report_id":existing["report_id"],
            "relationship_id":None,
            "replayed":True,
            "message":"This exact submission already exists, so it was not added again."
        }
        self._close_session(session, result)

        return result

    def _close_session(self, session:Record, result:Record)->None:
        session["status"]="decided"
        session["result"]=result
        session["decided_at"]=utc_now().isoformat()

    def _apply_plan(self, state:Record, plan:DecisionPlan)->None:
        if plan.problem is not None:
            state["problems"].append(plan.problem)

        if plan.report is not None:
            target=self._require_problem(state, plan.report["problem_id"])
            state["community_reports"].append(plan.report)
            refresh_counts(state, target)
            target["updated_at"]=plan.report["created_at"]

        if plan.relationship is not None:
            self._require_problem(state, plan.relationship["target_problem_id"])
            state["relationships"].append(plan.relationship)

        state["ai_feedback"].extend(plan.feedback)

    async def list_feedback(self)->list[Record]:
        return await self._read(lambda state:state["ai_feedback"])

    async def list_srs_versions(self, problem_id:str)->list[Record]:
        def reader(state:Record)->list[Record]:
            documents=[item for item in state["srs_documents"] if item["problem_id"] == problem_id]

            return sorted(documents, key=lambda item:item["version"])

        return await self._read(reader)

    async def save_srs(self, document:Record)->Record:
        def mutate(state:Record)->Record:
            versions=[item["version"] for item in state["srs_documents"] if item["problem_id"] == document["problem_id"]]
            saved={**document,"version":max(versions, default=0)+1}
            state["srs_documents"].append(saved)

            return saved

        return await self._write(mutate)

    async def update_srs(self, problem_id:str, version:int, changes:Record)->Record|None:
        def mutate(state:Record)->Record|None:
            for document in state["srs_documents"]:
                if document["problem_id"] == problem_id and document["version"] == version:
                    document.update(changes)
                    return document

            return None

        return await self._write(mutate)

    async def dashboard_snapshot(self)->Record:
        def reader(state:Record)->Record:
            return {name:state[name] for name in COLLECTIONS if name != "ai_feedback"}

        return await self._read(reader)

    async def seed(self, dataset:Record)->Record:
        return await self._write(lambda state:self._merge_dataset(state, dataset))

    async def reset(self, dataset:Record)->Record:
        backup=await asyncio.to_thread(self.store.backup)

        def mutate(state:Record)->Record:
            state.clear()
            state.update(empty_state())

            return self._merge_dataset(state, dataset)

        summary=await self._write(mutate)
        summary["backup"]=str(backup) if backup else None

        return summary

    def _merge_dataset(self, state:Record, dataset:Record)->Record:
        added:Counter=Counter()
        skipped:Counter=Counter()

        for name in SEEDED_COLLECTIONS:
            existing={record["id"] for record in state[name]}

            for record in dataset.get(name, []):
                if record["id"] in existing:
                    skipped[name]+=1
                else:
                    state[name].append({**record,"source":"synthetic"})
                    added[name]+=1

        self._merge_upvotes(state, dataset, added, skipped)

        for problem in state["problems"]:
            refresh_counts(state, problem)

        state["seeded_dataset_version"]=dataset.get("version")

        return {"added":dict(added),"skipped":dict(skipped),"dataset_version":dataset.get("version")}

    def _merge_upvotes(self, state:Record, dataset:Record, added:Counter, skipped:Counter)->None:
        existing={(item["problem_id"], item["user_id"]) for item in state["upvotes"]}

        for upvote in dataset.get("upvotes", []):
            if (upvote["problem_id"], upvote["user_id"]) in existing:
                skipped["upvotes"]+=1
            else:
                state["upvotes"].append({**upvote,"source":"synthetic"})
                added["upvotes"]+=1
