from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from ..utils import TRENDING_WINDOW_DAYS, parse_time, recent_upvote_counts
from .serializers import author_of, problem_summary, users_index

Record=dict[str, Any]

LIST_SIZE=6
RECENT_SIZE=6
ACTIVITY_SIZE=12
TOP_TAGS=10
TREND_MONTHS=9
TREND_WEEKS=12


def _month_key(moment:datetime)->str:
    return moment.strftime("%Y-%m")


def _previous_months(end:datetime, count:int)->list[datetime]:
    months=[]
    year=end.year
    month=end.month

    for _ in range(count):
        months.append(datetime(year, month, 1, tzinfo=end.tzinfo))
        month-=1

        if month == 0:
            month=12
            year-=1

    return list(reversed(months))


def _latest_activity(snapshot:Record)->datetime|None:
    moments=[]

    for name in ("problems", "community_reports", "upvotes", "comments", "solutions"):
        moments.extend(parse_time(item["created_at"]) for item in snapshot[name])

    return max(moments, default=None)


def _submission_trend(snapshot:Record, end:datetime)->list[Record]:
    problems=Counter(_month_key(parse_time(item["created_at"])) for item in snapshot["problems"])
    reports=Counter(_month_key(parse_time(item["created_at"])) for item in snapshot["community_reports"])
    trend=[]

    for month in _previous_months(end, TREND_MONTHS):
        key=_month_key(month)
        trend.append({"period":key,"label":month.strftime("%b %Y"),"problems":problems[key],"reports":reports[key]})

    return trend


def _week_start(moment:datetime)->datetime:
    start=moment-timedelta(days=moment.weekday())

    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def _engagement_trend(snapshot:Record, end:datetime)->list[Record]:
    upvotes=Counter(_week_start(parse_time(item["created_at"])) for item in snapshot["upvotes"])
    comments=Counter(_week_start(parse_time(item["created_at"])) for item in snapshot["comments"])
    last_week=_week_start(end)
    trend=[]

    for offset in range(TREND_WEEKS-1, -1, -1):
        week=last_week-timedelta(weeks=offset)
        trend.append({
            "period":week.date().isoformat(),
            "label":week.strftime("%d %b"),
            "upvotes":upvotes[week],
            "comments":comments[week]
        })

    return trend


def _distribution(values:list[str])->list[Record]:
    return [{"name":name,"count":count} for name, count in Counter(values).most_common()]


def _top_problems(problems:list[Record], key, users:dict[str, Record], limit:int=LIST_SIZE)->list[Record]:
    ranked=sorted(problems, key=lambda item:item["created_at"], reverse=True)
    ranked=sorted(ranked, key=key, reverse=True)

    return [problem_summary(problem, users) for problem in ranked[:limit]]


def _activity_timeline(snapshot:Record, users:dict[str, Record])->list[Record]:
    titles={problem["id"]:problem["title"] for problem in snapshot["problems"]}
    events=[]

    for problem in snapshot["problems"]:
        events.append(_event("problem", problem, problem["id"], problem["title"], users))

    for report in snapshot["community_reports"]:
        events.append(_event("report", report, report["problem_id"], titles.get(report["problem_id"], ""), users))

    for comment in snapshot["comments"]:
        events.append(_event("comment", comment, comment["problem_id"], titles.get(comment["problem_id"], ""), users))

    for solution in snapshot["solutions"]:
        events.append(_event("solution", solution, solution["problem_id"], solution["title"], users))

    events.sort(key=lambda event:event["created_at"], reverse=True)

    return events[:ACTIVITY_SIZE]


def _event(kind:str, record:Record, problem_id:str, title:str, users:dict[str, Record])->Record:
    return {
        "type":kind,
        "problem_id":problem_id,
        "title":title,
        "actor":author_of(record, users)["name"],
        "created_at":record["created_at"]
    }


def _workflow(snapshot:Record)->list[Record]:
    problems=snapshot["problems"]
    reports=snapshot["community_reports"]
    with_srs={document["problem_id"] for document in snapshot["srs_documents"]}
    solved=[problem for problem in problems if problem["status"] == "solved"]

    return [
        {"key":"submitted","label":"Submissions received","count":len(problems)+len(reports)},
        {"key":"reports","label":"Community reports","count":len(reports)},
        {"key":"problems","label":"Main problems","count":len(problems)},
        {"key":"related","label":"Related links","count":len(snapshot["relationships"])},
        {"key":"srs","label":"Problems with an SRS draft","count":len(with_srs)},
        {"key":"solutions","label":"Solutions published","count":len(snapshot["solutions"])},
        {"key":"solved","label":"Problems solved","count":len(solved)}
    ]


def _data_source(snapshot:Record)->Record:
    problems=snapshot["problems"]
    synthetic=sum(1 for problem in problems if problem.get("source") == "synthetic")

    return {
        "synthetic_problems":synthetic,
        "runtime_problems":len(problems)-synthetic,
        "includes_synthetic":synthetic > 0
    }


def build_dashboard(snapshot:Record)->Record:
    users=users_index(snapshot["users"])
    problems=snapshot["problems"]
    tags=[tag for problem in problems for tag in problem["tags"]]
    recent_upvotes=recent_upvote_counts(snapshot["upvotes"])
    latest=_latest_activity(snapshot)

    return {
        "data_source":_data_source(snapshot),
        "totals":{
            "problems":len(problems),
            "upvotes":len(snapshot["upvotes"]),
            "community_reports":len(snapshot["community_reports"]),
            "related_links":len(snapshot["relationships"]),
            "comments":len(snapshot["comments"]),
            "solutions":len(snapshot["solutions"])
        },
        "recent_submissions":_top_problems(problems, lambda item:item["created_at"], users, RECENT_SIZE),
        "trending":_top_problems(problems, lambda item:recent_upvotes[item["id"]], users),
        "trending_window_days":TRENDING_WINDOW_DAYS,
        "most_reported":_top_problems(problems, lambda item:item["report_count"], users),
        "most_supported":_top_problems(problems, lambda item:item["upvote_count"], users),
        "categories":_distribution([problem["category"] for problem in problems]),
        "statuses":_distribution([problem["status"] for problem in problems]),
        "tags":_distribution(tags)[:TOP_TAGS],
        "submission_trend":_submission_trend(snapshot, latest) if latest else [],
        "engagement_trend":_engagement_trend(snapshot, latest) if latest else [],
        "activity":_activity_timeline(snapshot, users),
        "workflow":_workflow(snapshot),
        "latest_activity_at":latest.isoformat() if latest else None
    }
