import hashlib
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from nlp.text import normalize_text

TRENDING_WINDOW_DAYS=30


def utc_now()->datetime:
    return datetime.now(timezone.utc)


def utc_now_iso()->str:
    return utc_now().isoformat()


def parse_time(value:str)->datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def new_id(prefix:str)->str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def submission_fingerprint(author_id:str, title:str, description:str)->str:
    raw=f"{author_id}\0{normalize_text(title)}\0{normalize_text(description)}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# Anchored to the newest upvote so static demo data stays meaningful.
def recent_upvote_counts(upvotes:list[dict[str, Any]])->Counter:
    if not upvotes:
        return Counter()

    latest=max(parse_time(upvote["created_at"]) for upvote in upvotes)
    start=latest-timedelta(days=TRENDING_WINDOW_DAYS)
    counts:Counter=Counter()

    for upvote in upvotes:
        if parse_time(upvote["created_at"]) >= start:
            counts[upvote["problem_id"]]+=1

    return counts
