from datetime import datetime, timezone
from statistics import mean
from typing import Any

from app.config.contexts import ContextName, get_context_config
from app.core.heap import MaxHeap
from app.core.priority import calculate_priority, waiting_time_minutes


def _timestamp(value: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def _simulate(context: ContextName | str, customers: list[dict[str, Any]], algorithm: str) -> dict[str, float | int | str]:
    context_name = ContextName(context)
    config = get_context_config(context_name)
    records: list[dict[str, Any]] = []
    for index, customer in enumerate(customers):
        record = dict(customer)
        if isinstance(record["arrival_time"], str):
            record["arrival_time"] = datetime.fromisoformat(
                record["arrival_time"].replace("Z", "+00:00")
            )
        if record.get("arrival_order") is None:
            record["arrival_order"] = index
        record["sequence"] = index
        records.append(record)
    if not records:
        return {
            "algorithm": algorithm,
            "average_waiting_time": 0.0,
            "maximum_waiting_time": 0.0,
            "average_turnaround_time": 0.0,
            "customers_served": 0,
        }

    remaining = records.copy()
    clock = min(_timestamp(record["arrival_time"]) for record in records)
    waits: list[float] = []
    turnarounds: list[float] = []
    while remaining:
        available = [record for record in remaining if _timestamp(record["arrival_time"]) <= clock]
        if not available:
            clock = min(_timestamp(record["arrival_time"]) for record in remaining)
            available = [record for record in remaining if _timestamp(record["arrival_time"]) <= clock]

        if algorithm == "FCFS":
            selected = min(
                available,
                key=lambda record: (
                    _timestamp(record["arrival_time"]),
                    record["arrival_order"],
                    record["sequence"],
                ),
            )
        elif algorithm == "STATIC_PRIORITY":
            def static_key(record: dict[str, Any]) -> tuple[float, float, int, int]:
                urgency = config.urgency_scores[record["urgency"].upper()]
                service = config.service_scores[record["service_type"].upper()]
                return (
                    0.5 * urgency + 0.2 * service,
                    -_timestamp(record["arrival_time"]),
                    -record["arrival_order"],
                    -record["sequence"],
                )

            selected = max(available, key=static_key)
        else:
            heap: MaxHeap[
                tuple[tuple[float, float, float, int, int], dict[str, Any]]
            ] = MaxHeap(key=lambda item: item[0])
            current_time = datetime.fromtimestamp(clock, tz=timezone.utc)
            for record in available:
                waiting = waiting_time_minutes(record["arrival_time"], current_time)
                score = calculate_priority(
                    context_name, record["urgency"], record["service_type"], waiting
                )
                tie_key = (
                    score,
                    waiting,
                    -_timestamp(record["arrival_time"]),
                    -record["arrival_order"],
                    -record["sequence"],
                )
                heap.push((tie_key, record))
            selected = heap.pop_max()[1]

        arrival = _timestamp(selected["arrival_time"])
        wait_minutes = max(0.0, (clock - arrival) / 60.0)
        finish = clock + selected["estimated_service_time"] * 60
        waits.append(wait_minutes)
        turnarounds.append(max(0.0, (finish - arrival) / 60.0))
        clock = finish
        remaining.remove(selected)

    return {
        "algorithm": algorithm,
        "average_waiting_time": round(mean(waits), 2),
        "maximum_waiting_time": round(max(waits), 2),
        "average_turnaround_time": round(mean(turnarounds), 2),
        "customers_served": len(records),
    }


def simulate_fcfs(context: ContextName | str, customers: list[dict[str, Any]]) -> dict[str, float | int | str]:
    return _simulate(context, customers, "FCFS")


def simulate_static_priority(context: ContextName | str, customers: list[dict[str, Any]]) -> dict[str, float | int | str]:
    return _simulate(context, customers, "STATIC_PRIORITY")


def simulate_dynamic_priority(context: ContextName | str, customers: list[dict[str, Any]]) -> dict[str, float | int | str]:
    return _simulate(context, customers, "DYNAMIC_PRIORITY_QUEUE")


def compare_algorithms(context: ContextName | str, customers: list[dict[str, Any]]) -> list[dict[str, float | int | str]]:
    dataset = [dict(customer) for customer in customers]
    return [
        simulate_fcfs(context, dataset),
        simulate_static_priority(context, dataset),
        simulate_dynamic_priority(context, dataset),
    ]
