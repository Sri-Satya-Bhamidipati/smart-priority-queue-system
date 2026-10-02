from datetime import datetime

from app.config.contexts import ContextName, get_context_config

URGENCY_WEIGHT = 0.50
WAITING_WEIGHT = 0.30
SERVICE_WEIGHT = 0.20
MAX_WAITING_MINUTES = 30.0


def waiting_time_minutes(arrival_time: datetime, now: datetime) -> float:
	if arrival_time.tzinfo is None:
		arrival_time = arrival_time.replace(tzinfo=now.tzinfo)
	if now.tzinfo is None:
		now = now.replace(tzinfo=arrival_time.tzinfo)
	return max(0.0, (now - arrival_time).total_seconds() / 60.0)


def waiting_score(waiting_minutes: float) -> float:
	return min(100.0, max(0.0, waiting_minutes) / MAX_WAITING_MINUTES * 100.0)


def calculate_priority(
	context: ContextName | str,
	urgency: str,
	service_type: str,
	waiting_minutes: float,
) -> float:
	config = get_context_config(context)
	urgency_key = urgency.strip().upper()
	service_key = service_type.strip().upper()
	if urgency_key not in config.urgency_scores:
		raise ValueError(f"Invalid urgency '{urgency}'.")
	if service_key not in config.service_scores:
		raise ValueError(f"Invalid service_type '{service_type}' for {ContextName(context).value}.")
	urgency_value = config.urgency_scores[urgency_key]
	wait_value = waiting_score(waiting_minutes)
	service_value = config.service_scores[service_key]
	return round(
		URGENCY_WEIGHT * urgency_value
		+ WAITING_WEIGHT * wait_value
		+ SERVICE_WEIGHT * service_value,
		2,
	)
