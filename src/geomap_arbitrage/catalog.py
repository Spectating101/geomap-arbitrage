from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .models import EvidenceSignal, GeoPoint, LegalStatus, MoneyRange, Opportunity, PersonProfile


def _point(value: Mapping[str, Any]) -> GeoPoint:
    return GeoPoint(name=str(value.get("name") or ""), lat=float(value["lat"]), lon=float(value["lon"]))


def _money(value: Mapping[str, Any]) -> MoneyRange:
    return MoneyRange(low=float(value["low"]), high=float(value["high"]), currency=str(value.get("currency") or "USD"))


def evidence_from_dict(value: Mapping[str, Any]) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(value["id"]),
        kind=str(value["kind"]),
        claim=str(value["claim"]),
        source=str(value["source"]),
        observed_at=str(value["observed_at"]),
        confidence=float(value["confidence"]),
        locator=str(value["locator"]) if value.get("locator") is not None else None,
        value=value.get("value"),
        unit=str(value["unit"]) if value.get("unit") is not None else None,
        method=str(value.get("method") or "observed"),
        metadata=dict(value.get("metadata") or {}),
    )


def opportunity_from_dict(value: Mapping[str, Any]) -> Opportunity:
    return Opportunity(
        id=str(value["id"]),
        archetype_id=str(value["archetype_id"]),
        title=str(value["title"]),
        thesis=str(value["thesis"]),
        category=str(value["category"]),
        location=_point(value["location"]),
        service_radius_km=float(value.get("service_radius_km") or 0),
        remote=bool(value.get("remote")),
        required_skills=tuple(str(x) for x in value.get("required_skills") or ()),
        helpful_skills=tuple(str(x) for x in value.get("helpful_skills") or ()),
        required_equipment=tuple(str(x) for x in value.get("required_equipment") or ()),
        startup_capital=_money(value["startup_capital"]),
        weekly_hours_required=float(value.get("weekly_hours_required") or 0),
        monthly_revenue=_money(value["monthly_revenue"]),
        monthly_cost=_money(value["monthly_cost"]),
        repeatability=float(value.get("repeatability") or 0),
        legal_status=LegalStatus(str(value.get("legal_status") or "unknown")),
        required_evidence_kinds=tuple(str(x) for x in value.get("required_evidence_kinds") or ()),
        execution_steps=tuple(str(x) for x in value.get("execution_steps") or ()),
        failure_modes=tuple(str(x) for x in value.get("failure_modes") or ()),
        evidence=tuple(evidence_from_dict(row) for row in value.get("evidence") or ()),
        metadata=dict(value.get("metadata") or {}),
    )


def profile_from_dict(value: Mapping[str, Any]) -> PersonProfile:
    return PersonProfile(
        id=str(value.get("id") or "profile"),
        location=_point(value["location"]),
        skills=tuple(str(x) for x in value.get("skills") or ()),
        capital_available=float(value.get("capital_available") or 0),
        currency=str(value.get("currency") or "USD"),
        weekly_hours=float(value.get("weekly_hours") or 0),
        mobility_km=float(value.get("mobility_km") or 0),
        equipment=tuple(str(x) for x in value.get("equipment") or ()),
        languages=tuple(str(x) for x in value.get("languages") or ()),
    )


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_profile(path: str | Path) -> PersonProfile:
    value = load_json(path)
    if not isinstance(value, Mapping):
        raise ValueError("profile file must contain one JSON object")
    return profile_from_dict(value)


def load_catalog(path: str | Path) -> tuple[Opportunity, ...]:
    value = load_json(path)
    rows: Sequence[Any]
    if isinstance(value, Mapping):
        rows = value.get("opportunities") or ()
    elif isinstance(value, list):
        rows = value
    else:
        raise ValueError("catalog must be a JSON array or object with opportunities[]")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("opportunities must be a sequence")
    return tuple(opportunity_from_dict(row) for row in rows if isinstance(row, Mapping))
