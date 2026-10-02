from datetime import datetime, timezone
from statistics import mean
from typing import Any


def calculate_metrics(
	waiting_customers: list[Any], served_customers: list[Any], now: datetime
) -> dict[str, float | int]:
	active_waits = [customer.current_wait_minutes(now) for customer in waiting_customers]
	completed_waits = [customer.waiting_time for customer in served_customers]
	all_waits = active_waits + completed_waits
	all_customers = waiting_customers + served_customers
	service_times = [customer.estimated_service_time for customer in all_customers]
	elapsed_hours = 0.0
	if all_customers:
		first_arrival = min(customer.arrival_timestamp() for customer in all_customers)
		current_time = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
		current_timestamp = current_time.timestamp()
		elapsed_hours = max(0.0, (current_timestamp - first_arrival) / 3600.0)
	throughput = len(served_customers) / elapsed_hours if elapsed_hours > 0 else 0.0
	return {
		"customers_waiting": len(waiting_customers),
		"average_waiting_time": round(mean(all_waits), 2) if all_waits else 0.0,
		"maximum_waiting_time": round(max(all_waits), 2) if all_waits else 0.0,
		"average_service_time": round(mean(service_times), 2) if service_times else 0.0,
		"throughput": round(throughput, 2),
		"queue_length": len(waiting_customers),
	}
