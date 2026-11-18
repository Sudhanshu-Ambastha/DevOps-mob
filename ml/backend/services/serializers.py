from typing import Any

Record=dict[str, Any]

GUEST_AUTHOR={"id":"guest","name":"Community member","role":"user"}


def public_user(user:Record)->Record:
    return {
        "id":user["id"],
        "name":user["name"],
        "role":user.get("role", "user"),
        "bio":user.get("bio", ""),
        "skills":user.get("skills", []),
        "created_at":user.get("created_at"),
        "source":user.get("source", "runtime")
    }


def private_user(user:Record)->Record:
    return {**public_user(user),"email":user.get("email", "")}


def users_index(users:list[Record])->dict[str, Record]:
    return {user["id"]:user for user in users}


def author_of(record:Record, users:dict[str, Record])->Record:
    user=users.get(record.get("author_id", ""))

    if user is None:
        return GUEST_AUTHOR

    return {"id":user["id"],"name":user["name"],"role":user.get("role", "user")}


def problem_summary(
    problem:Record,
    users:dict[str, Record],
    upvoted:set[str]|None=None,
    followed:set[str]|None=None
)->Record:
    return {
        "id":problem["id"],
        "title":problem["title"],
        "description":problem["description"],
        "category":problem["category"],
        "tags":problem["tags"],
        "outcome":problem.get("outcome", ""),
        "constraints":problem.get("constraints", ""),
        "is_paid":problem.get("is_paid", False),
        "budget_range":problem.get("budget_range", ""),
        "status":problem["status"],
        "author":author_of(problem, users),
        "upvote_count":problem.get("upvote_count", 0),
        "report_count":problem.get("report_count", 0),
        "comment_count":problem.get("comment_count", 0),
        "solution_count":problem.get("solution_count", 0),
        "viewer_has_upvoted":problem["id"] in (upvoted or set()),
        "viewer_is_following":problem["id"] in (followed or set()),
        "ai_processing_allowed":problem.get("ai_processing_allowed", False),
        "source":problem.get("source", "runtime"),
        "created_at":problem["created_at"],
        "updated_at":problem.get("updated_at", problem["created_at"])
    }


def report_view(report:Record, users:dict[str, Record])->Record:
    return {
        "id":report["id"],
        "problem_id":report["problem_id"],
        "title":report["title"],
        "description":report["description"],
        "outcome":report.get("outcome", ""),
        "constraints":report.get("constraints", ""),
        "tags":report.get("tags", []),
        "author":author_of(report, users),
        "source":report.get("source", "runtime"),
        "created_at":report["created_at"]
    }


def comment_view(comment:Record, users:dict[str, Record])->Record:
    return {
        "id":comment["id"],
        "problem_id":comment["problem_id"],
        "text":comment["text"],
        "author":author_of(comment, users),
        "created_at":comment["created_at"]
    }


def solution_view(solution:Record, users:dict[str, Record], problem:Record|None=None)->Record:
    return {
        "id":solution["id"],
        "problem_id":solution["problem_id"],
        "problem_title":problem["title"] if problem else "",
        "title":solution["title"],
        "description":solution["description"],
        "repo_url":solution.get("repo_url", ""),
        "tech_stack":solution.get("tech_stack", []),
        "author":author_of(solution, users),
        "source":solution.get("source", "runtime"),
        "created_at":solution["created_at"]
    }


def srs_view(document:Record)->Record:
    return {
        "problem_id":document["problem_id"],
        "version":document["version"],
        "markdown":document["markdown"],
        "status":document["status"],
        "model":document["model"],
        "is_complete":document["is_complete"],
        "warnings":document.get("warnings", []),
        "generated_at":document["generated_at"],
        "updated_at":document["updated_at"]
    }
