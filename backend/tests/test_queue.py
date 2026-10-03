from datetime import datetime, timedelta, timezone

import pytest

from app.core.queue_engine import QueueEngine


NOW = datetime(2026, 10, 2, 22, 30, tzinfo=timezone.utc)


def add(engine, customer_id, *, urgency="NORMAL", service_type="CASH_WITHDRAWAL", age=0, service_time=5):
	return engine.add_customer(
		customer_id=customer_id,
		arrival_time=NOW - timedelta(minutes=age),
		urgency=urgency,
		service_type=service_type,
		estimated_service_time=service_time,
		now=NOW,
	)


def test_empty_queue_operations():
	engine = QueueEngine("BANK")
	assert engine.get_queue(NOW) == []
	assert engine.get_next_customer(NOW) is None
	assert engine.serve_next_customer(NOW) is None


def test_single_customer_is_next_and_served():
	engine = QueueEngine("BANK")
	add(engine, "one")
	assert engine.get_next_customer(NOW).customer_id == "one"
	served = engine.serve_next_customer(NOW)
	assert served.customer_id == "one"
	assert served.status == "SERVED"
	assert engine.get_queue(NOW) == []


def test_multiple_customers_schedule_highest_priority():
	engine = QueueEngine("BANK")
	add(engine, "low", urgency="LOW")
	add(engine, "high", urgency="HIGH")
	assert engine.get_next_customer(NOW).customer_id == "high"


def test_critical_customer_precedes_routine_customer():
	engine = QueueEngine("HOSPITAL")
	add(engine, "routine", urgency="ROUTINE", service_type="PRESCRIPTION")
	add(engine, "emergency", urgency="EMERGENCY", service_type="EMERGENCY_CARE")
	assert engine.serve_next_customer(NOW).customer_id == "emergency"


def test_equal_priority_prefers_longer_wait():
	engine = QueueEngine("BANK")
	add(engine, "newer", urgency="NORMAL", age=0)
	add(engine, "older", urgency="NORMAL", age=10)
	assert engine.get_next_customer(NOW).customer_id == "older"


def test_equal_priority_and_wait_prefers_earlier_arrival_then_insertion():
	engine = QueueEngine("BANK")
	add(engine, "first")
	add(engine, "second")
	assert engine.get_next_customer(NOW).customer_id == "first"
	assert [item.customer_id for item in engine.get_queue(NOW)] == ["first", "second"]


def test_long_waiting_low_priority_can_overtake_new_critical_customer():
	engine = QueueEngine("BANK")
	add(engine, "aged-low", urgency="LOW", service_type="FRAUD_REVIEW", age=30)
	add(engine, "new-critical", urgency="CRITICAL", service_type="CASH_WITHDRAWAL")
	assert engine.get_next_customer(NOW).customer_id == "aged-low"


def test_duplicate_customer_id_rejected_even_after_service():
	engine = QueueEngine("BANK")
	add(engine, "same")
	with pytest.raises(ValueError, match="Duplicate"):
		add(engine, "same")
	engine.serve_next_customer(NOW)
	with pytest.raises(ValueError, match="Duplicate"):
		add(engine, "same")


@pytest.mark.parametrize(("urgency", "service_type", "service_time", "message"), [
	("IMPOSSIBLE", "CASH_WITHDRAWAL", 5, "urgency"),
	("NORMAL", "NOT_A_SERVICE", 5, "service_type"),
	("NORMAL", "CASH_WITHDRAWAL", -1, "greater than zero"),
	("NORMAL", "CASH_WITHDRAWAL", 0, "greater than zero"),
])
def test_invalid_customer_values_rejected(urgency, service_type, service_time, message):
	engine = QueueEngine("BANK")
	with pytest.raises(ValueError, match=message):
		add(engine, "invalid", urgency=urgency, service_type=service_type, service_time=service_time)


def test_all_equal_priority_are_served_deterministically():
	engine = QueueEngine("BANK")
	for customer_id in ["A", "B", "C"]:
		add(engine, customer_id)
	assert [engine.serve_next_customer(NOW).customer_id for _ in range(3)] == ["A", "B", "C"]


def test_dynamic_insertion_while_queue_is_active():
	engine = QueueEngine("BANK")
	add(engine, "first", urgency="LOW")
	assert engine.serve_next_customer(NOW).customer_id == "first"
	add(engine, "regular", urgency="NORMAL")
	add(engine, "inserted-critical", urgency="CRITICAL")
	assert engine.get_next_customer(NOW).customer_id == "inserted-critical"


def test_priority_and_wait_refresh_as_time_passes():
	engine = QueueEngine("BANK")
	customer = add(engine, "aging", urgency="LOW", age=0)
	earlier = customer.priority_score
	later = NOW + timedelta(minutes=15)
	engine.update_waiting_times(later)
	assert customer.waiting_time == 15
	assert customer.priority_score > earlier


def test_queue_length_stays_constant_when_only_waiting_time_advances():
	engine = QueueEngine("BANK")
	for index in range(5):
		add(engine, f"aging-{index}", urgency="LOW", age=index)

	before = engine.get_metrics(NOW)
	before_priorities = {
		customer.customer_id: customer.priority_score
		for customer in engine.get_queue(NOW)
	}
	later = NOW + timedelta(minutes=15)
	engine.update_waiting_times(later)
	after = engine.get_metrics(later)
	after_priorities = {
		customer.customer_id: customer.priority_score
		for customer in engine.get_queue(later)
	}

	assert before["queue_length"] == before["customers_waiting"] == 5
	assert after["queue_length"] == after["customers_waiting"] == 5
	assert len(engine.get_queue(later)) == 5
	assert before_priorities != after_priorities


def test_invalid_context_rejected():
	with pytest.raises(ValueError, match="Invalid context"):
		QueueEngine("AIRPORT")
