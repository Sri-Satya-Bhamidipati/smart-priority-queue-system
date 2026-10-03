from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.core.queue_engine import QueueEngine

client = TestClient(app)


def test_malformed_json_rejected():
	response = client.post("/api/queue/add", content="{not-json", headers={"content-type": "application/json"})
	assert response.status_code == 422


def test_schema_rejects_invalid_datetime_empty_id_and_zero_service():
	base = {
		"context": "BANK",
		"customer_id": "valid",
		"arrival_time": "2026-10-02T22:15:00",
		"urgency": "HIGH",
		"service_type": "CASH_WITHDRAWAL",
		"estimated_service_time": 5,
	}
	for changed in [
		{**base, "customer_id": "   "},
		{**base, "arrival_time": "yesterday"},
		{**base, "estimated_service_time": 0},
	]:
		assert client.post("/api/queue/add", json=changed).status_code == 422


def test_unknown_context_rejected_by_api():
	assert client.get("/api/queue", params={"context": "AIRPORT"}).status_code == 422


def test_queue_api_add_next_serve_metrics_and_reset():
	client.post("/api/queue/reset", params={"context": "BANK"})
	response = client.post("/api/queue/add", json={
		"context": "BANK",
		"customer_id": "api-customer",
		"arrival_time": "2026-10-02T22:15:00Z",
		"urgency": "HIGH",
		"service_type": "CASH_WITHDRAWAL",
		"estimated_service_time": 5,
	})
	assert response.status_code == 200
	assert response.json()["customer_id"] == "api-customer"
	assert client.get("/api/queue/next", params={"context": "BANK"}).json()["customer_id"] == "api-customer"
	assert client.get("/api/queue/metrics", params={"context": "BANK"}).json()["queue_length"] == 1
	assert client.post("/api/queue/serve", params={"context": "BANK"}).json()["status"] == "SERVED"
	assert client.post("/api/queue/reset", params={"context": "BANK"}).status_code == 200


def test_comparison_runs_all_algorithms_on_same_dataset():
	body = {
		"context": "BANK",
		"customers": [
			{"customer_id": "compare-1", "arrival_time": "2026-10-02T22:15:00Z", "urgency": "LOW", "service_type": "BALANCE_INQUIRY", "estimated_service_time": 5},
			{"customer_id": "compare-2", "arrival_time": "2026-10-02T22:15:00Z", "urgency": "CRITICAL", "service_type": "FRAUD_REVIEW", "estimated_service_time": 10},
		],
	}
	response = client.post("/api/queue/compare", json=body)
	assert response.status_code == 200
	results = response.json()["results"]
	assert [item["algorithm"] for item in results] == ["FCFS", "STATIC_PRIORITY", "DYNAMIC_PRIORITY_QUEUE"]
	assert all(item["customers_served"] == 2 for item in results)
	assert all("average_turnaround_time" in item for item in results)


def test_comparison_keeps_arrival_order_and_does_not_mutate_live_queue():
	client.post("/api/queue/reset", params={"context": "BANK"})
	arrival = "2026-10-03T00:00:00Z"
	for customer_id, urgency, service_type, service_time in [
		("first-low", "LOW", "BALANCE_INQUIRY", 5),
		("second-critical", "CRITICAL", "FRAUD_REVIEW", 10),
	]:
		assert client.post("/api/queue/add", json={
			"context": "BANK",
			"customer_id": customer_id,
			"arrival_time": arrival,
			"urgency": urgency,
			"service_type": service_type,
			"estimated_service_time": service_time,
		}).status_code == 200

	queue_response = client.get("/api/queue", params={"context": "BANK"}).json()
	assert queue_response["queue_length"] == 2
	assert [item["customer_id"] for item in queue_response["queue"]] == [
		"second-critical", "first-low"
	]
	assert [item["arrival_order"] for item in queue_response["queue"]] == [1, 0]
	before_metrics = client.get("/api/queue/metrics", params={"context": "BANK"}).json()
	comparison = client.post("/api/queue/compare", json={
		"context": "BANK",
		"customers": queue_response["queue"],
	})
	assert comparison.status_code == 200
	results = comparison.json()["results"]
	after_queue = client.get("/api/queue", params={"context": "BANK"}).json()
	after_metrics = client.get("/api/queue/metrics", params={"context": "BANK"}).json()

	assert results[0]["average_waiting_time"] < results[1]["average_waiting_time"]
	assert after_queue["queue_length"] == queue_response["queue_length"] == 2
	assert {item["customer_id"] for item in after_queue["queue"]} == {
		"first-low", "second-critical"
	}
	assert after_metrics["queue_length"] == before_metrics["queue_length"] == 2
	client.post("/api/queue/reset", params={"context": "BANK"})


def test_batch_is_atomic_on_duplicate_id():
	engine = QueueEngine("BANK")
	input_time = datetime(2026, 10, 2, 22, 15, tzinfo=timezone.utc)
	customers = [
		{"customer_id": "duplicate", "arrival_time": input_time, "urgency": "HIGH", "service_type": "CASH_WITHDRAWAL", "estimated_service_time": 5},
		{"customer_id": "duplicate", "arrival_time": input_time, "urgency": "LOW", "service_type": "CASH_WITHDRAWAL", "estimated_service_time": 5},
	]
	try:
		engine.add_customers(customers)
	except ValueError:
		pass
	assert engine.get_queue(input_time) == []
