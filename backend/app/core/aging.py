from datetime import datetime

from app.core.priority import waiting_time_minutes, waiting_score

__all__ = ["waiting_time_minutes", "waiting_score"]


def calculate_waiting_time(arrival_time: datetime, now: datetime) -> float:
	return waiting_time_minutes(arrival_time, now)
