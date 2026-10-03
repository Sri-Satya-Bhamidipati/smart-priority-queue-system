from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.config.contexts import ContextName, get_context_config
from app.core.heap import MaxHeap
from app.core.metrics import calculate_metrics
from app.core.priority import calculate_priority, waiting_time_minutes
from app.core.validators import validate_customer_fields


@dataclass
class Customer:
	customer_id: str
	arrival_time: datetime
	urgency: str
	service_type: str
	estimated_service_time: int
	priority_score: float = 0.0
	waiting_time: float = 0.0
	status: str = "WAITING"
	served_at: datetime | None = None
	_sequence: int = field(default=0, repr=False)

	def arrival_timestamp(self) -> float:
		value = self.arrival_time
		if value.tzinfo is None:
			value = value.replace(tzinfo=timezone.utc)
		return value.timestamp()

	def current_wait_minutes(self, now: datetime) -> float:
		return waiting_time_minutes(self.arrival_time, now)

	def as_dict(self, now: datetime, *, include_arrival_order: bool = False) -> dict[str, Any]:
		wait = self.current_wait_minutes(now) if self.status == "WAITING" else self.waiting_time
		data: dict[str, Any] = {
			"customer_id": self.customer_id,
			"arrival_time": self.arrival_time.isoformat(),
			"priority_score": self.priority_score,
			"waiting_time": round(wait, 2),
			"status": self.status,
			"urgency": self.urgency,
			"service_type": self.service_type,
			"estimated_service_time": self.estimated_service_time,
		}
		if include_arrival_order:
			data["arrival_order"] = self._sequence
		return data


class QueueEngine:
	def __init__(self, context: ContextName | str = ContextName.BANK) -> None:
		try:
			self.context = ContextName(context)
		except ValueError:
			get_context_config(context)
			raise
		get_context_config(self.context)
		self._customers: dict[str, Customer] = {}
		self._served: list[Customer] = []
		self._sequence = 0
		self._heap: MaxHeap[Customer] = MaxHeap(key=self._heap_key)

	@staticmethod
	def _heap_key(customer: Customer) -> tuple[float, float, float, int]:
		return (
			customer.priority_score,
			customer.waiting_time,
			-customer.arrival_timestamp(),
			-customer._sequence,
		)

	def _refresh(self, now: datetime) -> None:
		waiting = list(self._customers.values())
		for customer in waiting:
			customer.waiting_time = customer.current_wait_minutes(now)
			customer.priority_score = calculate_priority(
				self.context, customer.urgency, customer.service_type, customer.waiting_time
			)
		self._heap.rebuild(waiting)

	def add_customer(
		self,
		customer_id: str,
		arrival_time: datetime,
		urgency: str,
		service_type: str,
		estimated_service_time: int,
		now: datetime | None = None,
	) -> Customer:
		validate_customer_fields(
			customer_id, arrival_time, urgency, service_type, estimated_service_time, self.context
		)
		if customer_id in self._customers or any(item.customer_id == customer_id for item in self._served):
			raise ValueError(f"Duplicate customer_id '{customer_id}'.")
		customer = Customer(
			customer_id=customer_id.strip(),
			arrival_time=arrival_time,
			urgency=urgency.strip().upper(),
			service_type=service_type.strip().upper(),
			estimated_service_time=estimated_service_time,
			_sequence=self._sequence,
		)
		current_time = now or datetime.now(timezone.utc)
		customer.waiting_time = customer.current_wait_minutes(current_time)
		customer.priority_score = calculate_priority(
			self.context, customer.urgency, customer.service_type, customer.waiting_time
		)
		self._sequence += 1
		self._customers[customer.customer_id] = customer
		self._heap.push(customer)
		return customer

	def add_customers(self, customers: list[dict[str, Any]], now: datetime | None = None) -> list[Customer]:
		seen: set[str] = set()
		for item in customers:
			validate_customer_fields(
				item["customer_id"], item["arrival_time"], item["urgency"], item["service_type"],
				item["estimated_service_time"], self.context,
			)
			customer_id = item["customer_id"].strip()
			if customer_id in seen or customer_id in self._customers or any(
				served.customer_id == customer_id for served in self._served
			):
				raise ValueError(f"Duplicate customer_id '{customer_id}'.")
			seen.add(customer_id)
		return [self.add_customer(**item, now=now) for item in customers]

	def get_next_customer(self, now: datetime | None = None) -> Customer | None:
		self._refresh(now or datetime.now(timezone.utc))
		return self._heap.peek()

	def serve_next_customer(self, now: datetime | None = None) -> Customer | None:
		current_time = now or datetime.now(timezone.utc)
		self._refresh(current_time)
		customer = self._heap.pop_max()
		if customer is None:
			return None
		customer.waiting_time = customer.current_wait_minutes(current_time)
		customer.status = "SERVED"
		customer.served_at = current_time
		self._customers.pop(customer.customer_id)
		self._served.append(customer)
		return customer

	def get_queue(self, now: datetime | None = None) -> list[Customer]:
		self._refresh(now or datetime.now(timezone.utc))
		copy = self._heap.copy()
		ordered: list[Customer] = []
		while (customer := copy.pop_max()) is not None:
			ordered.append(customer)
		return ordered

	def update_waiting_times(self, now: datetime | None = None) -> list[Customer]:
		self._refresh(now or datetime.now(timezone.utc))
		return list(self._customers.values())

	def calculate_priority(self, customer: Customer, now: datetime | None = None) -> float:
		wait = customer.current_wait_minutes(now or datetime.now(timezone.utc))
		return calculate_priority(self.context, customer.urgency, customer.service_type, wait)

	def get_metrics(self, now: datetime | None = None) -> dict[str, float | int]:
		current_time = now or datetime.now(timezone.utc)
		return calculate_metrics(list(self._customers.values()), self._served.copy(), current_time)

	def reset_queue(self) -> None:
		self._customers.clear()
		self._served.clear()
		self._sequence = 0
		self._heap = MaxHeap(key=self._heap_key)
