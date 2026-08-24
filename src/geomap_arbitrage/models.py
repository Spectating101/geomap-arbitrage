from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Sequence


class OpportunityStatus(str, Enum):
    RECOMMENDED = "recommended"
    RESEARCH_REQUIRED = "research_required"
    BLOCKED = "blocked"


class LegalStatus(str, Enum):
    ALLOWED = "allowed"
    PERMIT_REQUIRED = "permit_required"
    UNKNOWN = "unknown"
    PROHIBITED = "prohibited"


@dataclass(frozen=True)
class GeoPoint:
    name: str
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not -90 <= self.lat <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= self.lon <= 180:
            raise ValueError("longitude must be between -180 and 180")


@dataclass(frozen=True)
class MoneyRange:
    low: float
    high: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.low < 0 or self.high < 0:
            raise ValueError("money ranges cannot be negative")
        if self.high < self.low:
            raise ValueError("money range high must be >= low")
        if not self.currency.strip():
            raise ValueError("currency is required")

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2


@dataclass(frozen=True)
class EvidenceSignal:
    id: str
    kind: str
    claim: str
    source: str
    observed_at: str
    confidence: float
    locator: str | None = None
    value: Any = None
    unit: str | None = None
    method: str = "observed"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("evidence signal id is required")
        if not self.kind.strip():
            raise ValueError("evidence signal kind is required")
        if not self.claim.strip():
            raise ValueError("evidence signal claim is required")
        if not self.source.strip():
            raise ValueError("evidence signal source is required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("evidence confidence must be between 0 and 1")
        parse_iso_date(self.observed_at)


@dataclass(frozen=True)
class PersonProfile:
    id: str
    location: GeoPoint
    skills: tuple[str, ...] = ()
    capital_available: float = 0.0
    currency: str = "USD"
    weekly_hours: float = 0.0
    mobility_km: float = 0.0
    equipment: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.capital_available < 0:
            raise ValueError("capital_available cannot be negative")
        if self.weekly_hours < 0:
            raise ValueError("weekly_hours cannot be negative")
        if self.mobility_km < 0:
            raise ValueError("mobility_km cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")

    def constraint_snapshot(self, *, include_coordinates: bool = False) -> dict[str, Any]:
        """Privacy-minimized profile representation for evidence receipts.

        Names/contact details are intentionally absent from the domain model. Exact
        coordinates are omitted by default: the assessment already records the
        computed distance used by the mobility gate, so the receipt can preserve the
        decision basis without persisting a precise origin point.
        """
        location = {"name": self.location.name}
        if include_coordinates:
            location.update({"lat": self.location.lat, "lon": self.location.lon})
        return {
            "location": location,
            "skills": sorted(normalize_terms(self.skills)),
            "capital_available": self.capital_available,
            "currency": self.currency,
            "weekly_hours": self.weekly_hours,
            "mobility_km": self.mobility_km,
            "equipment": sorted(normalize_terms(self.equipment)),
            "languages": sorted(normalize_terms(self.languages)),
        }


@dataclass(frozen=True)
class Opportunity:
    id: str
    archetype_id: str
    title: str
    thesis: str
    category: str
    location: GeoPoint
    service_radius_km: float
    remote: bool
    required_skills: tuple[str, ...]
    helpful_skills: tuple[str, ...]
    required_equipment: tuple[str, ...]
    startup_capital: MoneyRange
    weekly_hours_required: float
    monthly_revenue: MoneyRange
    monthly_cost: MoneyRange
    repeatability: float
    legal_status: LegalStatus
    required_evidence_kinds: tuple[str, ...]
    execution_steps: tuple[str, ...]
    failure_modes: tuple[str, ...]
    evidence: tuple[EvidenceSignal, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.startup_capital.currency != self.monthly_revenue.currency:
            raise ValueError("startup capital and revenue currency must match")
        if self.monthly_cost.currency != self.monthly_revenue.currency:
            raise ValueError("monthly cost and revenue currency must match")
        if self.service_radius_km < 0:
            raise ValueError("service_radius_km cannot be negative")
        if self.weekly_hours_required < 0:
            raise ValueError("weekly_hours_required cannot be negative")
        if not 0 <= self.repeatability <= 1:
            raise ValueError("repeatability must be between 0 and 1")
        if not self.execution_steps:
            raise ValueError("opportunity requires at least one execution step")


@dataclass(frozen=True)
class GateOutcome:
    gate_id: str
    passed: bool
    blocking: bool
    reason: str


@dataclass(frozen=True)
class Assessment:
    opportunity_id: str
    status: OpportunityStatus
    score: float
    fit_score: float
    economics_score: float
    evidence_score: float
    execution_score: float
    distance_km: float
    estimated_monthly_surplus: MoneyRange
    estimated_payback_months: float | None
    gates: tuple[GateOutcome, ...]
    blockers: tuple[str, ...]
    research_questions: tuple[str, ...]
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        return body


@dataclass(frozen=True)
class RankedOpportunity:
    opportunity: Opportunity
    assessment: Assessment

    def as_dict(self) -> dict[str, Any]:
        return {
            "opportunity": {
                **asdict(self.opportunity),
                "legal_status": self.opportunity.legal_status.value,
            },
            "assessment": self.assessment.as_dict(),
        }


@dataclass(frozen=True)
class LivelihoodPlan:
    profile_id: str
    primary_opportunity_id: str | None
    secondary_opportunity_id: str | None
    research_queue: tuple[str, ...]
    next_actions: tuple[str, ...]
    blocked_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_terms(values: Sequence[str]) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


def parse_iso_date(value: str) -> date:
    raw = str(value).strip()
    if not raw:
        raise ValueError("date is required")
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {value}") from exc
