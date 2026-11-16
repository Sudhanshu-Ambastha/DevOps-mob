import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .json_files import atomic_write_json, read_json
from .errors import PaidEndpointBlocked, ProviderQuotaExhausted, ProviderRateLimited


def utc_now()->datetime:
    return datetime.now(timezone.utc)


def seconds_until_next_utc_day(now:datetime|None=None)->int:
    current=now or utc_now()
    next_day=(current+timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    return int((next_day-current).total_seconds())


class UsageGuard:
    def __init__(self, path:Path, budgets:dict[str, float]):
        self.path=path
        self.budgets=budgets
        self._lock=threading.Lock()
        self._state=self._load()

    def _load(self)->dict[str, Any]:
        state=read_json(self.path, default=None)

        if not isinstance(state, dict):
            return self._empty_state()

        return state

    def _empty_state(self)->dict[str, Any]:
        return {"day":utc_now().date().isoformat(),"used":{},"blocked_until":{},"tripped":{}}

    def _roll_day(self)->None:
        today=utc_now().date().isoformat()

        if self._state.get("day") != today:
            self._state["day"]=today
            self._state["used"]={}

    def ensure_available(self, provider:str, amount:float=1.0)->None:
        with self._lock:
            self._roll_day()
            self._raise_if_tripped(provider)
            self._raise_if_cooling_down(provider)
            used=self._state["used"].get(provider, 0.0)
            budget=self.budgets.get(provider)

            if budget is not None and used+amount > budget:
                raise ProviderQuotaExhausted(
                    f"The local daily budget for {provider} is used up. It resets at 00:00 UTC.",
                    provider=provider,
                    retry_after=seconds_until_next_utc_day()
                )

    def _raise_if_tripped(self, provider:str)->None:
        reason=self._state.get("tripped", {}).get(provider)

        if reason:
            raise PaidEndpointBlocked(reason, provider=provider)

    def _raise_if_cooling_down(self, provider:str)->None:
        blocked=self._state.get("blocked_until", {}).get(provider)

        if not blocked:
            return

        remaining=(datetime.fromisoformat(blocked)-utc_now()).total_seconds()

        if remaining <= 0:
            del self._state["blocked_until"][provider]
            return

        raise ProviderRateLimited(
            f"{provider} asked us to wait, so no request was sent. Please try again later.",
            provider=provider,
            retry_after=int(remaining)+1
        )

    def record(self, provider:str, amount:float=1.0)->None:
        with self._lock:
            self._roll_day()
            self._state["used"][provider]=self._state["used"].get(provider, 0.0)+amount
            self._save()

    def block_for(self, provider:str, seconds:int)->None:
        with self._lock:
            until=utc_now()+timedelta(seconds=seconds)
            self._state.setdefault("blocked_until", {})[provider]=until.isoformat()
            self._save()

    def trip(self, provider:str, reason:str)->None:
        with self._lock:
            self._state.setdefault("tripped", {})[provider]=reason
            self._save()

    def snapshot(self, provider:str)->dict[str, Any]:
        with self._lock:
            self._roll_day()

            return {
                "used_today":round(self._state["used"].get(provider, 0.0), 3),
                "daily_budget":self.budgets.get(provider),
                "blocked_until":self._state.get("blocked_until", {}).get(provider),
                "tripped_reason":self._state.get("tripped", {}).get(provider)
            }

    def _save(self)->None:
        atomic_write_json(self.path, self._state)
