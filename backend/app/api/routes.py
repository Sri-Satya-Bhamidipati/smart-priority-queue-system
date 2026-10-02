from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import AddCustomerRequest, BatchCustomersRequest, ComparisonRequest
from app.config.contexts import CONTEXTS, ContextName
from app.core.queue_engine import QueueEngine
from app.core.simulation import compare_algorithms
from app.core.validators import validate_customer_fields

router = APIRouter(prefix="/api")
engines = {context: QueueEngine(context) for context in ContextName}


def _engine(context: str) -> QueueEngine:
	try:
		return engines[ContextName(context.upper())]
	except ValueError as exc:
		valid = ", ".join(item.value for item in ContextName)
		raise HTTPException(status_code=422, detail=f"Invalid context. Choose one of: {valid}.") from exc


def _customer_data(customer, now: datetime | None = None) -> dict[str, Any]:
	return customer.as_dict(now or datetime.now().astimezone())


@router.get("/contexts")
def list_contexts() -> dict[str, Any]:
	return {
		"contexts": [
			{
				"name": context.value,
				"urgency_scores": CONTEXTS[context].urgency_scores,
				"service_types": CONTEXTS[context].service_scores,
			}
			for context in ContextName
		]
	}


@router.post("/queue/add")
def add_customer(request: AddCustomerRequest) -> dict[str, Any]:
	engine = _engine(request.context)
	data = request.model_dump(exclude={"context"})
	try:
		customer = engine.add_customer(**data)
	except ValueError as exc:
		raise HTTPException(status_code=422, detail=str(exc)) from exc
	return _customer_data(customer)


@router.post("/queue/batch")
def add_batch(request: BatchCustomersRequest) -> dict[str, Any]:
	engine = _engine(request.context)
	try:
		customers = engine.add_customers([customer.model_dump() for customer in request.customers])
	except ValueError as exc:
		raise HTTPException(status_code=422, detail=str(exc)) from exc
	now = datetime.now().astimezone()
	return {"context": engine.context.value, "customers": [_customer_data(item, now) for item in customers]}


@router.get("/queue")
def get_queue(context: str = Query(default="BANK")) -> dict[str, Any]:
	engine = _engine(context)
	now = datetime.now().astimezone()
	customers = engine.get_queue(now)
	return {
		"context": engine.context.value,
		"queue": [_customer_data(item, now) for item in customers],
		"queue_length": len(customers),
	}


@router.get("/queue/next")
def get_next_customer(context: str = Query(default="BANK")) -> dict[str, Any] | None:
	engine = _engine(context)
	customer = engine.get_next_customer()
	return _customer_data(customer) if customer else None


@router.post("/queue/serve")
def serve_next_customer(context: str = Query(default="BANK")) -> dict[str, Any] | None:
	engine = _engine(context)
	customer = engine.serve_next_customer()
	return _customer_data(customer) if customer else None


@router.get("/queue/metrics")
def get_metrics(context: str = Query(default="BANK")) -> dict[str, Any]:
	engine = _engine(context)
	return {"context": engine.context.value, **engine.get_metrics()}


@router.post("/queue/reset")
def reset_queue(context: str = Query(default="BANK")) -> dict[str, str]:
	engine = _engine(context)
	engine.reset_queue()
	return {"context": engine.context.value, "message": "Queue reset."}


@router.post("/queue/compare")
def compare(request: ComparisonRequest) -> dict[str, Any]:
	engine = _engine(request.context)
	try:
		customers = [customer.model_dump() for customer in request.customers]
		for customer in customers:
			validate_customer_fields(**customer, context=engine.context)
		results = compare_algorithms(engine.context, customers)
	except ValueError as exc:
		raise HTTPException(status_code=422, detail=str(exc)) from exc
	return {"context": engine.context.value, "results": results}
