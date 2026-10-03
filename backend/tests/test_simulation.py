from copy import deepcopy
from datetime import datetime, timedelta, timezone

from app.core.queue_engine import QueueEngine
from app.core.simulation import compare_algorithms


START = datetime(2026, 10, 3, 0, 0, tzinfo=timezone.utc)


def customer(customer_id, arrival_time, urgency, service_type, service_time, arrival_order):
	return {
		"customer_id": customer_id,
		"arrival_time": arrival_time,
		"urgency": urgency,
		"service_type": service_type,
		"estimated_service_time": service_time,
		"arrival_order": arrival_order,
	}


def test_comparison_runs_fcfs_static_and_dynamic_rules_on_the_same_dataset():
	dataset = [
		customer("first-low", START, "LOW", "BALANCE_INQUIRY", 5, 0),
		customer("second-critical", START, "CRITICAL", "FRAUD_REVIEW", 10, 1),
	]
	original = deepcopy(dataset)

	results = compare_algorithms("BANK", dataset)
	fcfs, static, dynamic = results

	assert [result["algorithm"] for result in results] == [
		"FCFS", "STATIC_PRIORITY", "DYNAMIC_PRIORITY_QUEUE"
	]
	assert all(result["customers_served"] == len(dataset) for result in results)
	assert fcfs["average_waiting_time"] == 2.5
	assert fcfs["maximum_waiting_time"] == 5.0
	assert fcfs["average_turnaround_time"] == 10.0
	assert static["average_waiting_time"] == dynamic["average_waiting_time"] == 5.0
	assert static["maximum_waiting_time"] == dynamic["maximum_waiting_time"] == 10.0
	assert static["average_turnaround_time"] == dynamic["average_turnaround_time"] == 12.5
	assert dataset == original


def test_dynamic_aging_can_change_order_from_static_priority():
	dataset = [
		customer("lead-critical", START, "CRITICAL", "FRAUD_REVIEW", 30, 0),
		customer("aged-low", START, "LOW", "FRAUD_REVIEW", 20, 1),
		customer(
			"later-normal",
			START + timedelta(minutes=20),
			"NORMAL",
			"FRAUD_REVIEW",
			5,
			2,
		),
	]

	fcfs, static, dynamic = compare_algorithms("BANK", dataset)

	assert static["maximum_waiting_time"] == 35.0
	assert dynamic["maximum_waiting_time"] == fcfs["maximum_waiting_time"] == 30.0
	assert static["average_waiting_time"] == 15.0
	assert dynamic["average_waiting_time"] == fcfs["average_waiting_time"] == 20.0
	assert static["average_turnaround_time"] == 33.33
	assert dynamic["average_turnaround_time"] == fcfs["average_turnaround_time"] == 38.33


def test_fcfs_uses_arrival_order_not_priority_order_for_equal_arrivals():
	engine = QueueEngine("BANK")
	engine.add_customers(
		[
			{
				"customer_id": "first-low",
				"arrival_time": START,
				"urgency": "LOW",
				"service_type": "BALANCE_INQUIRY",
				"estimated_service_time": 5,
			},
			{
				"customer_id": "second-critical",
				"arrival_time": START,
				"urgency": "CRITICAL",
				"service_type": "FRAUD_REVIEW",
				"estimated_service_time": 10,
			},
		],
		now=START,
	)
	priority_order = engine.get_queue(START)
	assert [item.customer_id for item in priority_order] == ["second-critical", "first-low"]

	dataset = [
		item.as_dict(START, include_arrival_order=True)
		for item in priority_order
	]
	fcfs, static, dynamic = compare_algorithms("BANK", dataset)

	assert fcfs["average_waiting_time"] == 2.5
	assert static["average_waiting_time"] == dynamic["average_waiting_time"] == 5.0


def test_comparison_uses_context_configuration_and_actual_dataset_values():
	bank = [
		customer("bank-a", START, "HIGH", "BALANCE_INQUIRY", 5, 0),
		customer("bank-b", START, "NORMAL", "FRAUD_REVIEW", 20, 1),
	]
	hospital = [
		customer("hospital-a", START, "URGENT", "PRESCRIPTION", 5, 0),
		customer("hospital-b", START, "ROUTINE", "EMERGENCY_CARE", 20, 1),
	]
	short_bank = [dict(item, estimated_service_time=2) for item in bank]

	bank_results = compare_algorithms("BANK", bank)
	hospital_results = compare_algorithms("HOSPITAL", hospital)
	short_bank_results = compare_algorithms("BANK", short_bank)

	assert bank_results[1]["maximum_waiting_time"] == 20.0
	assert hospital_results[1]["maximum_waiting_time"] == 5.0
	assert short_bank_results[1]["maximum_waiting_time"] == 2.0


def test_comparison_operates_on_a_snapshot_without_mutating_live_queue():
	engine = QueueEngine("BANK")
	engine.add_customers(
		[
			{
				"customer_id": f"live-{index}",
				"arrival_time": START - timedelta(minutes=index),
				"urgency": "LOW" if index % 2 else "HIGH",
				"service_type": "FRAUD_REVIEW",
				"estimated_service_time": 5 + index,
			}
			for index in range(5)
		],
		now=START,
	)
	live_before = {
		item.customer_id: (item.waiting_time, item.priority_score, item.status)
		for item in engine.get_queue(START)
	}
	snapshot = [
		item.as_dict(START, include_arrival_order=True)
		for item in engine.get_queue(START)
	]
	snapshot_before = deepcopy(snapshot)

	results = compare_algorithms("BANK", snapshot)

	live_after = {
		item.customer_id: (item.waiting_time, item.priority_score, item.status)
		for item in engine.get_queue(START)
	}
	assert live_after == live_before
	assert len(engine.get_queue(START)) == 5
	assert engine.get_metrics(START)["queue_length"] == 5
	assert snapshot == snapshot_before
	assert all(result["customers_served"] == 5 for result in results)

