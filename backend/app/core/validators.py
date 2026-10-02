from datetime import datetime

from app.config.contexts import ContextName, get_context_config


def validate_context(context: str) -> ContextName:
	try:
		return ContextName(context)
	except ValueError as exc:
		get_context_config(context)
		raise exc


def validate_customer_fields(
	customer_id: str,
	arrival_time: datetime,
	urgency: str,
	service_type: str,
	estimated_service_time: int,
	context: ContextName | str,
) -> None:
	if not customer_id or not customer_id.strip():
		raise ValueError("customer_id must not be empty.")
	if not isinstance(arrival_time, datetime):
		raise ValueError("arrival_time must be a valid ISO 8601 datetime.")
	if estimated_service_time <= 0:
		raise ValueError("estimated_service_time must be greater than zero.")
	config = get_context_config(context)
	if urgency.strip().upper() not in config.urgency_scores:
		raise ValueError(f"Invalid urgency '{urgency}' for {ContextName(context).value}.")
	if service_type.strip().upper() not in config.service_scores:
		raise ValueError(f"Invalid service_type '{service_type}' for {ContextName(context).value}.")
