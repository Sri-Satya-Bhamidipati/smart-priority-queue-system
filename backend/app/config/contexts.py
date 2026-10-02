from dataclasses import dataclass
from enum import StrEnum


class ContextName(StrEnum):
	HOSPITAL = "HOSPITAL"
	BANK = "BANK"
	GOVERNMENT = "GOVERNMENT"
	COLLEGE = "COLLEGE"


SERVICE_CATEGORY_SCORES = {
	"CRITICAL_COMPLEX": 100.0,
	"MODERATE": 70.0,
	"STANDARD": 40.0,
	"QUICK": 20.0,
}


@dataclass(frozen=True)
class ContextConfig:
	urgency_scores: dict[str, float]
	service_types: dict[str, str]

	@property
	def service_scores(self) -> dict[str, float]:
		return {
			service: SERVICE_CATEGORY_SCORES[category]
			for service, category in self.service_types.items()
		}


CONTEXTS: dict[ContextName, ContextConfig] = {
	ContextName.HOSPITAL: ContextConfig(
		urgency_scores={"EMERGENCY": 100, "CRITICAL": 80, "URGENT": 60, "ROUTINE": 30},
		service_types={
			"EMERGENCY_CARE": "CRITICAL_COMPLEX",
			"SURGERY": "CRITICAL_COMPLEX",
			"SPECIALIST_CONSULTATION": "MODERATE",
			"MEDICAL_CONSULTATION": "MODERATE",
			"PRESCRIPTION": "STANDARD",
			"GENERAL_INQUIRY": "QUICK",
		},
	),
	ContextName.BANK: ContextConfig(
		urgency_scores={"CRITICAL": 90, "HIGH": 70, "NORMAL": 40, "LOW": 20},
		service_types={
			"FRAUD_REVIEW": "CRITICAL_COMPLEX",
			"LOAN_APPROVAL": "CRITICAL_COMPLEX",
			"DOCUMENT_VERIFICATION": "MODERATE",
			"ACCOUNT_OPENING": "MODERATE",
			"CASH_WITHDRAWAL": "QUICK",
			"BALANCE_INQUIRY": "QUICK",
		},
	),
	ContextName.GOVERNMENT: ContextConfig(
		urgency_scores={"CRITICAL": 90, "HIGH": 70, "NORMAL": 40, "LOW": 20},
		service_types={
			"LEGAL_CASE": "CRITICAL_COMPLEX",
			"PASSPORT_APPLICATION": "MODERATE",
			"DOCUMENT_VERIFICATION": "MODERATE",
			"CERTIFICATE_REQUEST": "STANDARD",
			"FORM_SUBMISSION": "QUICK",
		},
	),
	ContextName.COLLEGE: ContextConfig(
		urgency_scores={"CRITICAL": 90, "HIGH": 70, "NORMAL": 40, "LOW": 20},
		service_types={
			"EXAM_ACCOMMODATION": "CRITICAL_COMPLEX",
			"SCHOLARSHIP_REVIEW": "MODERATE",
			"DOCUMENT_VERIFICATION": "MODERATE",
			"COURSE_REGISTRATION": "STANDARD",
			"ID_CARD": "QUICK",
		},
	),
}


def get_context_config(context: ContextName | str) -> ContextConfig:
	try:
		return CONTEXTS[ContextName(context)]
	except (ValueError, KeyError) as exc:
		valid = ", ".join(item.value for item in ContextName)
		raise ValueError(f"Invalid context. Choose one of: {valid}.") from exc
