import re
from collections import Counter
from datetime import timedelta
from pathlib import Path
from typing import Any

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError, PyMongoError

from nlp.json_files import atomic_write_json

from ..utils import recent_upvote_counts, utc_now, utc_now_iso
from .base import DecisionPlan, ProblemQuery, Record, Repository
from .json_repository import SEEDED_COLLECTIONS, RecordNotFound
from .json_store import StoreBusyError

HIDE_ID={"_id":0}
LINK_COLLECTIONS=("upvotes", "follows")

INDEXES={
    "users":[("id", True), ("email", True)],
    "problems":[("id", True), ("fingerprint", False), ("category", False), ("status", False), ("tags", False), ("created_at", False)],
    "community_reports":[("id", True), ("problem_id", False), ("fingerprint", False)],
    "relationships":[("id", True), ("source_problem_id", False), ("target_problem_id", False)],
    "comments":[("id", True), ("problem_id", False)],
    "solutions":[("id", True), ("problem_id", False)],
    "match_sessions":[("id", True), ("client_request_id", False)],
    "ai_feedback":[("id", True), ("session_id", False)]
}

SORT_FIELDS={
    "newest":"created_at",
    "most_upvoted":"upvote_count",
    "most_reported":"report_count",
    "most_solutions":"solution_count"
}


class MongoUnavailable(Exception):
    pass


class MongoRepository(Repository):
    def __init__(self, uri:str, database:str, timeout_ms:int=5000, backup_dir:Path|None=None):
        self.client=AsyncMongoClient(uri, serverSelectionTimeoutMS=timeout_ms, tz_aware=False)
        self.db=self.client[database]
        self.database_name=database
        self.backup_dir=backup_dir

    async def prepare(self)->None:
        try:
            await self.client.admin.command("ping")
        except PyMongoError as error:
            raise MongoUnavailable(f"MongoDB is not reachable: {error}") from error

        for name, fields in INDEXES.items():
            for field, unique in fields:
                options={"unique":True,"partialFilterExpression":{field:{"$type":"string"}}} if unique else {}
                await self.db[name].create_index([(field, ASCENDING)], **options)

        for name in LINK_COLLECTIONS:
            await self.db[name].create_index([("problem_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
            await self.db[name].create_index([("user_id", ASCENDING)])

        await self.db.srs_documents.create_index([("problem_id", ASCENDING), ("version", ASCENDING)], unique=True)

    async def close(self)->None:
        await self.client.close()

    async def is_empty(self)->bool:
        return await self.db.problems.count_documents({}, limit=1) == 0

    async def _all(self, name:str, query:Record|None=None, sort:list|None=None)->list[Record]:
        cursor=self.db[name].find(query or {}, HIDE_ID)

        if sort:
            cursor=cursor.sort(sort)

        return await cursor.to_list(None)

    async def _one(self, name:str, query:Record)->Record|None:
        return await self.db[name].find_one(query, HIDE_ID)

    async def _require_problem(self, problem_id:str)->Record:
        problem=await self._one("problems", {"id":problem_id})

        if problem is None:
            raise RecordNotFound(problem_id)

        return problem

    async def _refresh_counts(self, problem_id:str, extra:Record|None=None)->Record:
        counts={
            "upvote_count":await self.db.upvotes.count_documents({"problem_id":problem_id}),
            "report_count":await self.db.community_reports.count_documents({"problem_id":problem_id}),
            "comment_count":await self.db.comments.count_documents({"problem_id":problem_id}),
            "solution_count":await self.db.solutions.count_documents({"problem_id":problem_id})
        }
        await self.db.problems.update_one({"id":problem_id}, {"$set":{**counts, **(extra or {})}})

        return counts

    async def list_users(self)->list[Record]:
        return await self._all("users")

    async def find_user_by_email(self, email:str)->Record|None:
        return await self._one("users", {"email":email})

    async def get_user(self, user_id:str)->Record|None:
        return await self._one("users", {"id":user_id})

    async def create_user(self, user:Record)->Record:
        await self.db.users.insert_one(dict(user))

        return user

    async def update_user(self, user_id:str, changes:Record)->Record|None:
        await self.db.users.update_one({"id":user_id}, {"$set":changes})

        return await self.get_user(user_id)

    def _problem_filter(self, query:ProblemQuery)->Record:
        conditions:Record={}

        if query.category:
            conditions["category"]=query.category

        if query.status:
            conditions["status"]=query.status

        if query.tag:
            conditions["tags"]=query.tag.lower()

        search=query.search.strip()

        if search:
            pattern={"$regex":re.escape(search),"$options":"i"}
            conditions["$or"]=[{"title":pattern}, {"description":pattern}, {"tags":pattern}]

        return conditions

    async def find_problems(self, query:ProblemQuery)->tuple[list[Record], int]:
        conditions=self._problem_filter(query)
        total=await self.db.problems.count_documents(conditions)
        start=(query.page-1)*query.page_size

        if query.sort in SORT_FIELDS:
            order=[(SORT_FIELDS[query.sort], DESCENDING), ("created_at", DESCENDING)]
            cursor=self.db.problems.find(conditions, HIDE_ID).sort(order).skip(start).limit(query.page_size)

            return (await cursor.to_list(None), total)

        matches=await self._all("problems", conditions, [("created_at", DESCENDING)])
        recent=recent_upvote_counts(await self._all("upvotes"))
        matches.sort(key=lambda problem:recent[problem["id"]], reverse=True)

        return (matches[start:start+query.page_size], total)

    async def list_all_problems(self)->list[Record]:
        return await self._all("problems")

    async def get_problem(self, problem_id:str)->Record|None:
        return await self._one("problems", {"id":problem_id})

    async def get_problems(self, problem_ids:list[str])->list[Record]:
        return await self._all("problems", {"id":{"$in":problem_ids}})

    async def _toggle_link(self, name:str, problem_id:str, user_id:str)->bool:
        await self._require_problem(problem_id)
        removed=await self.db[name].delete_one({"problem_id":problem_id,"user_id":user_id})

        if removed.deleted_count:
            return False

        link={"problem_id":problem_id,"user_id":user_id,"created_at":utc_now_iso(),"source":"runtime"}

        try:
            await self.db[name].insert_one(link)
        except DuplicateKeyError:
            pass

        return True

    async def toggle_upvote(self, problem_id:str, user_id:str)->tuple[bool, int]:
        active=await self._toggle_link("upvotes", problem_id, user_id)
        counts=await self._refresh_counts(problem_id)

        return (active, counts["upvote_count"])

    async def toggle_follow(self, problem_id:str, user_id:str)->bool:
        return await self._toggle_link("follows", problem_id, user_id)

    async def upvoted_problem_ids(self, user_id:str)->set[str]:
        return {item["problem_id"] for item in await self._all("upvotes", {"user_id":user_id})}

    async def followed_problem_ids(self, user_id:str)->set[str]:
        return {item["problem_id"] for item in await self._all("follows", {"user_id":user_id})}

    async def list_reports(self, problem_id:str)->list[Record]:
        return await self._all("community_reports", {"problem_id":problem_id}, [("created_at", ASCENDING)])

    async def list_relationships(self, problem_id:str)->list[Record]:
        query={"$or":[{"source_problem_id":problem_id}, {"target_problem_id":problem_id}]}

        return await self._all("relationships", query)

    async def list_comments(self, problem_id:str)->list[Record]:
        return await self._all("comments", {"problem_id":problem_id}, [("created_at", ASCENDING)])

    async def add_comment(self, comment:Record)->Record:
        await self._require_problem(comment["problem_id"])
        await self.db.comments.insert_one(dict(comment))
        await self._refresh_counts(comment["problem_id"], {"updated_at":comment["created_at"]})

        return comment

    async def list_solutions(self, problem_id:str|None=None)->list[Record]:
        query={"problem_id":problem_id} if problem_id is not None else {}

        return await self._all("solutions", query, [("created_at", DESCENDING)])

    async def get_solution(self, solution_id:str)->Record|None:
        return await self._one("solutions", {"id":solution_id})

    async def add_solution(self, solution:Record)->Record:
        problem=await self._require_problem(solution["problem_id"])
        await self.db.solutions.insert_one(dict(solution))
        extra={"updated_at":solution["created_at"]}

        if problem["status"] == "open":
            extra["status"]="in-progress"

        await self._refresh_counts(solution["problem_id"], extra)

        return solution

    async def create_match_session(self, session:Record, ttl_hours:int)->Record:
        cutoff=(utc_now()-timedelta(hours=ttl_hours)).isoformat()
        await self.db.match_sessions.delete_many({"status":"open","created_at":{"$lt":cutoff}})
        await self.db.match_sessions.insert_one(dict(session))

        return session

    async def get_match_session(self, session_id:str)->Record|None:
        return await self._one("match_sessions", {"id":session_id})

    async def find_open_session_by_request(self, client_request_id:str)->Record|None:
        return await self._one("match_sessions", {"status":"open","client_request_id":client_request_id})

    async def _find_existing_submission(self, fingerprint:str)->Record|None:
        problem=await self._one("problems", {"fingerprint":fingerprint})

        if problem is not None:
            return {"problem_id":problem["id"],"report_id":None}

        report=await self._one("community_reports", {"fingerprint":fingerprint})

        if report is not None:
            return {"problem_id":report["problem_id"],"report_id":report["id"]}

        return None

    async def _close_session(self, session_id:str, result:Record)->None:
        changes={"status":"decided","result":result,"decided_at":utc_now_iso()}
        await self.db.match_sessions.update_one({"id":session_id}, {"$set":changes})

    async def commit_decision(self, session_id:str, plan:DecisionPlan)->Record:
        # Claiming the session first stops two requests from applying the same decision.
        claimed=await self.db.match_sessions.find_one_and_update(
            {"id":session_id,"status":"open"},
            {"$set":{"status":"deciding"}}
        )

        if claimed is None:
            session=await self.get_match_session(session_id)

            if session is None:
                raise RecordNotFound(session_id)

            if session["status"] == "decided":
                return {**session["result"],"replayed":True}

            raise StoreBusyError("This decision is already being saved. Please try again.")

        try:
            existing=await self._find_existing_submission(plan.fingerprint)

            if existing is not None:
                result={
                    **plan.result,
                    "problem_id":existing["problem_id"],
                    "report_id":existing["report_id"],
                    "relationship_id":None,
                    "replayed":True,
                    "message":"This exact submission already exists, so it was not added again."
                }
                await self._close_session(session_id, result)

                return result

            await self._apply_plan(plan)
            await self._close_session(session_id, plan.result)

            return plan.result
        except BaseException:
            await self.db.match_sessions.update_one({"id":session_id,"status":"deciding"}, {"$set":{"status":"open"}})
            raise

    async def _apply_plan(self, plan:DecisionPlan)->None:
        if plan.report is not None:
            await self._require_problem(plan.report["problem_id"])

        if plan.relationship is not None:
            await self._require_problem(plan.relationship["target_problem_id"])

        if plan.problem is not None:
            await self.db.problems.insert_one(dict(plan.problem))

        if plan.report is not None:
            await self.db.community_reports.insert_one(dict(plan.report))
            await self._refresh_counts(plan.report["problem_id"], {"updated_at":plan.report["created_at"]})

        if plan.relationship is not None:
            await self.db.relationships.insert_one(dict(plan.relationship))

        if plan.feedback:
            await self.db.ai_feedback.insert_many([dict(item) for item in plan.feedback])

    async def list_feedback(self)->list[Record]:
        return await self._all("ai_feedback")

    async def list_srs_versions(self, problem_id:str)->list[Record]:
        return await self._all("srs_documents", {"problem_id":problem_id}, [("version", ASCENDING)])

    async def save_srs(self, document:Record)->Record:
        for _ in range(5):
            latest=await self.db.srs_documents.find_one({"problem_id":document["problem_id"]}, sort=[("version", DESCENDING)])
            saved={**document,"version":(latest["version"] if latest else 0)+1}

            try:
                await self.db.srs_documents.insert_one(dict(saved))
                return saved
            except DuplicateKeyError:
                continue

        raise StoreBusyError("The SRS could not be saved. Please try again.")

    async def update_srs(self, problem_id:str, version:int, changes:Record)->Record|None:
        await self.db.srs_documents.update_one({"problem_id":problem_id,"version":version}, {"$set":changes})

        return await self._one("srs_documents", {"problem_id":problem_id,"version":version})

    async def dashboard_snapshot(self)->Record:
        names=("users", "problems", "community_reports", "relationships", "upvotes", "follows", "comments", "solutions", "match_sessions", "srs_documents")

        return {name:await self._all(name) for name in names}

    async def seed(self, dataset:Record)->Record:
        added:Counter=Counter()
        skipped:Counter=Counter()

        for name in SEEDED_COLLECTIONS:
            await self._upsert_missing(name, dataset.get(name, []), lambda record:{"id":record["id"]}, added, skipped)

        upvotes=dataset.get("upvotes", [])
        await self._upsert_missing("upvotes", upvotes, lambda record:{"problem_id":record["problem_id"],"user_id":record["user_id"]}, added, skipped)

        for problem in await self._all("problems", {}, None):
            await self._refresh_counts(problem["id"])

        return {"added":dict(added),"skipped":dict(skipped),"dataset_version":dataset.get("version")}

    async def _upsert_missing(self, name:str, records:list[Record], key, added:Counter, skipped:Counter)->None:
        if not records:
            return

        operations=[UpdateOne(key(record), {"$setOnInsert":{**record,"source":"synthetic"}}, upsert=True) for record in records]
        result=await self.db[name].bulk_write(operations, ordered=False)

        if result.upserted_count:
            added[name]+=result.upserted_count

        if len(records)-result.upserted_count:
            skipped[name]+=len(records)-result.upserted_count

    async def backup(self)->Path|None:
        if self.backup_dir is None:
            return None

        snapshot=await self.dashboard_snapshot()
        snapshot["ai_feedback"]=await self.list_feedback()
        stamp=utc_now().strftime("%Y%m%dT%H%M%SZ")
        target=self.backup_dir/f"mongodb-{self.database_name}-{stamp}.json"
        atomic_write_json(target, snapshot)

        return target

    async def reset(self, dataset:Record)->Record:
        backup=await self.backup()

        for name in (*INDEXES, *LINK_COLLECTIONS, "srs_documents"):
            await self.db[name].delete_many({})

        summary=await self.seed(dataset)
        summary["backup"]=str(backup) if backup else None

        return summary
