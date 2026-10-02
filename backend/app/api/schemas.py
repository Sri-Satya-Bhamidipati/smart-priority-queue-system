from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerInput(BaseModel):
	model_config = ConfigDict(str_strip_whitespace=True)

	customer_id: str = Field(min_length=1)
	arrival_time: datetime
	urgency: str = Field(min_length=1)
	service_type: str = Field(min_length=1)
	estimated_service_time: int = Field(gt=0)

	@field_validator("urgency", "service_type", mode="before")
	@classmethod
	def normalize_names(cls, value: str) -> str:
		if isinstance(value, str):
			return value.strip().upper()
		return value


class AddCustomerRequest(CustomerInput):
	context: str = "BANK"


class BatchCustomersRequest(BaseModel):
	context: str = "BANK"
	customers: list[CustomerInput]


class ComparisonRequest(BatchCustomersRequest):
	pass
