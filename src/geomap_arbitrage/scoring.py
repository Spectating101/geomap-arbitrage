from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Iterable

from .geometry import haversine_km
from .models import (
    Assessment,
    GateOutcome,
    LegalStatus,
    MoneyRange,
    Opportunity,
    OpportunityStatus,
    PersonProfile,
    normalize_terms,
    parse_iso_date,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _gate(gate_id: str, passed: bool, blocking: bool, reason: str) -> GateOutcome:
    return GateOutcome(gate_id=gate_id, passed=passed, blocking=blocking, reason=reason)


def _status(gates: Iterable[GateOutcome]) -> OpportunityStatus:
    failed = [gate for gate in gates if not gate.passed]
    if any(gate.blocking for gate in failed):
        return OpportunityStatus.BLOCKED
    if failed:
        return OpportunityStatus.RESEARCH_REQUIRED
    return OpportunityStatus.RECOMMENDED


def assess_opportunity(
    profile: PersonProfile,
    opportunity: Opportunity,
    *,
    as_of: str | date,
    max_evidence_age_days: int = 120,
    min_evidence_confidence: float = 0.60,
    min_independent_sources: int = 2,
) -> Assessment:
    """Deterministically assess one person/place/opportunity combination.

    The score is a ranking heuristic, not an income forecast. Status is governed by
    explicit gates so a high numeric score cannot rescue a prohibited, unaffordable,
    unreachable, stale, or economically negative opportunity.
    """
    if max_evidence_age_days <= 0:
        raise ValueError("max_evidence_age_days must be positive")
    if isinstance(as_of, str):
        as_of_date = parse_iso_date(as_of)
    else:
        as_of_date = as_of

    profile_skills = normalize_terms(profile.skills)
    required_skills = normalize_terms(opportunity.required_skills)
    helpful_skills = normalize_terms(opportunity.helpful_skills)
    equipment = normalize_terms(profile.equipment)
    required_equipment = normalize_terms(opportunity.required_equipment)

    missing_skills = sorted(required_skills - profile_skills)
    missing_equipment = sorted(required_equipment - equipment)
    distance_km = 0.0 if opportunity.remote else haversine_km(profile.location, opportunity.location)

    gates: list[GateOutcome] = []
    research_questions: list[str] = []
    rationale: list[str] = []

    skill_pass = not missing_skills
    gates.append(_gate(
        "skill_fit",
        skill_pass,
        False,
        "Required skills are present." if skill_pass else f"Missing required skills: {', '.join(missing_skills)}",
    ))
    if missing_skills:
        research_questions.append(f"Can the missing skills be learned, partnered, or subcontracted: {', '.join(missing_skills)}?")

    equipment_pass = not missing_equipment
    gates.append(_gate(
        "equipment_fit",
        equipment_pass,
        False,
        "Required equipment is already available." if equipment_pass else f"Missing equipment: {', '.join(missing_equipment)}",
    ))
    if missing_equipment:
        research_questions.append(f"What is the cheapest lawful way to acquire or rent: {', '.join(missing_equipment)}?")

    if profile.currency != opportunity.startup_capital.currency:
        capital_pass = False
        capital_blocking = False
        capital_reason = (
            f"Currency mismatch: profile={profile.currency}, opportunity={opportunity.startup_capital.currency}; "
            "convert before treating affordability as known."
        )
        research_questions.append("What exchange rate and conversion costs apply to startup capital and operating cash flow?")
    elif profile.capital_available < opportunity.startup_capital.low:
        capital_pass = False
        capital_blocking = True
        capital_reason = (
            f"Available capital {profile.capital_available:.2f} is below minimum startup estimate "
            f"{opportunity.startup_capital.low:.2f} {profile.currency}."
        )
    elif profile.capital_available < opportunity.startup_capital.high:
        capital_pass = False
        capital_blocking = False
        capital_reason = (
            f"Capital covers the low startup estimate but not the high estimate "
            f"({opportunity.startup_capital.low:.2f}-{opportunity.startup_capital.high:.2f} {profile.currency})."
        )
        research_questions.append("Can startup cost be validated or staged below the available-capital ceiling?")
    else:
        capital_pass = True
        capital_blocking = False
        capital_reason = "Available capital covers the full startup estimate."
    gates.append(_gate("capital", capital_pass, capital_blocking, capital_reason))

    time_pass = profile.weekly_hours >= opportunity.weekly_hours_required
    gates.append(_gate(
        "time",
        time_pass,
        True,
        "Weekly time budget is sufficient." if time_pass else (
            f"Requires {opportunity.weekly_hours_required:.1f} h/week but profile has {profile.weekly_hours:.1f} h/week."
        ),
    ))

    if opportunity.remote:
        mobility_pass = True
        mobility_reason = "Opportunity is marked remote."
    else:
        allowed_distance = min(profile.mobility_km, opportunity.service_radius_km)
        mobility_pass = distance_km <= allowed_distance
        mobility_reason = (
            f"Distance {distance_km:.1f} km is within executable radius {allowed_distance:.1f} km."
            if mobility_pass
            else f"Distance {distance_km:.1f} km exceeds executable radius {allowed_distance:.1f} km."
        )
    gates.append(_gate("mobility", mobility_pass, True, mobility_reason))

    if opportunity.legal_status == LegalStatus.ALLOWED:
        legal_pass, legal_blocking = True, False
        legal_reason = "Current catalog marks the activity as allowed under declared assumptions."
    elif opportunity.legal_status == LegalStatus.PROHIBITED:
        legal_pass, legal_blocking = False, True
        legal_reason = "Catalog marks the activity as prohibited; do not recommend execution."
    elif opportunity.legal_status == LegalStatus.PERMIT_REQUIRED:
        legal_pass, legal_blocking = False, False
        legal_reason = "Permit or registration is required before execution."
        research_questions.append("Which permit, registration, insurance, tax, or licensing requirements must be satisfied?")
    else:
        legal_pass, legal_blocking = False, False
        legal_reason = "Legal/regulatory status is unresolved."
        research_questions.append("Verify local legal, licensing, tax, and platform-rule constraints before execution.")
    gates.append(_gate("legal", legal_pass, legal_blocking, legal_reason))

    fresh_signals = []
    stale_ids = []
    for signal in opportunity.evidence:
        age = (as_of_date - parse_iso_date(signal.observed_at)).days
        if age < 0:
            stale_ids.append(signal.id)
            continue
        if age <= max_evidence_age_days:
            fresh_signals.append((signal, age))
        else:
            stale_ids.append(signal.id)

    fresh_kinds = {signal.kind.strip().lower() for signal, _ in fresh_signals}
    required_kinds = normalize_terms(opportunity.required_evidence_kinds)
    missing_kinds = sorted(required_kinds - fresh_kinds)
    unique_sources = {signal.source.strip().lower() for signal, _ in fresh_signals if signal.source.strip()}
    avg_confidence = (
        sum(signal.confidence for signal, _ in fresh_signals) / len(fresh_signals)
        if fresh_signals
        else 0.0
    )
    coverage = 1.0 if not required_kinds else len(required_kinds & fresh_kinds) / len(required_kinds)
    source_diversity = _clamp(len(unique_sources) / max(min_independent_sources, 1))
    freshness = (
        sum(_clamp(1 - age / max_evidence_age_days) for _, age in fresh_signals) / len(fresh_signals)
        if fresh_signals
        else 0.0
    )
    evidence_score = round(100 * (
        0.50 * avg_confidence
        + 0.25 * coverage
        + 0.15 * source_diversity
        + 0.10 * freshness
    ), 2)

    evidence_pass = (
        not missing_kinds
        and len(unique_sources) >= min_independent_sources
        and avg_confidence >= min_evidence_confidence
        and bool(fresh_signals)
    )
    evidence_reasons = []
    if missing_kinds:
        evidence_reasons.append(f"missing fresh evidence kinds: {', '.join(missing_kinds)}")
    if len(unique_sources) < min_independent_sources:
        evidence_reasons.append(f"only {len(unique_sources)} independent source(s)")
    if avg_confidence < min_evidence_confidence:
        evidence_reasons.append(f"average confidence {avg_confidence:.2f} below {min_evidence_confidence:.2f}")
    if stale_ids:
        evidence_reasons.append(f"stale/future evidence excluded: {', '.join(stale_ids)}")
    gates.append(_gate(
        "evidence",
        evidence_pass,
        False,
        "Evidence coverage, freshness, diversity, and confidence are sufficient."
        if evidence_pass
        else "; ".join(evidence_reasons) or "No usable evidence.",
    ))
    if not evidence_pass:
        research_questions.append("Refresh or add independent evidence until all required evidence classes are covered.")

    conservative_surplus = opportunity.monthly_revenue.low - opportunity.monthly_cost.high
    optimistic_surplus = opportunity.monthly_revenue.high - opportunity.monthly_cost.low
    surplus = MoneyRange(
        low=max(0.0, conservative_surplus) if optimistic_surplus >= 0 else 0.0,
        high=max(0.0, optimistic_surplus),
        currency=opportunity.monthly_revenue.currency,
    )

    if profile.currency != opportunity.monthly_revenue.currency:
        economics_pass, economics_blocking = False, False
        economics_reason = "Economics cannot be treated as decision-ready until currency conversion is resolved."
        research_questions.append("Convert revenue/cost ranges into the profile currency with fees and volatility buffer.")
    elif optimistic_surplus <= 0:
        economics_pass, economics_blocking = False, True
        economics_reason = (
            f"Even optimistic monthly surplus is non-positive ({optimistic_surplus:.2f} {profile.currency})."
        )
    elif conservative_surplus <= 0:
        economics_pass, economics_blocking = False, False
        economics_reason = (
            "Mid/optimistic economics may be positive, but the conservative revenue-cost range still crosses zero."
        )
        research_questions.append("Validate price, utilization, demand frequency, and variable costs until downside surplus is positive.")
    else:
        economics_pass, economics_blocking = True, False
        economics_reason = (
            f"Conservative monthly surplus is positive at {conservative_surplus:.2f} {profile.currency}."
        )
    gates.append(_gate("economics", economics_pass, economics_blocking, economics_reason))

    required_fit = 1.0 if not required_skills else len(required_skills & profile_skills) / len(required_skills)
    helpful_fit = 1.0 if not helpful_skills else len(helpful_skills & profile_skills) / len(helpful_skills)
    equipment_fit = 1.0 if not required_equipment else len(required_equipment & equipment) / len(required_equipment)
    language_bonus = 0.05 if profile.languages else 0.0
    fit_score = round(100 * _clamp(0.70 * required_fit + 0.20 * helpful_fit + 0.10 * equipment_fit + language_bonus), 2)

    revenue_mid = opportunity.monthly_revenue.midpoint
    cost_mid = opportunity.monthly_cost.midpoint
    net_mid = max(0.0, revenue_mid - cost_mid)
    margin = net_mid / revenue_mid if revenue_mid > 0 else 0.0
    startup_mid = opportunity.startup_capital.midpoint
    payback = startup_mid / net_mid if net_mid > 0 else None
    margin_score = _clamp(margin / 0.50)
    payback_score = 0.0 if payback is None else _clamp(1 / (1 + payback / 3))
    downside_score = 1.0 if conservative_surplus > 0 else 0.35 if optimistic_surplus > 0 else 0.0
    economics_score = round(100 * (0.45 * margin_score + 0.35 * payback_score + 0.20 * downside_score), 2)

    if profile.currency == opportunity.startup_capital.currency and opportunity.startup_capital.high > 0:
        capital_ease = _clamp(profile.capital_available / opportunity.startup_capital.high)
    else:
        capital_ease = 0.5
    time_ease = 1.0 if opportunity.weekly_hours_required <= 0 else _clamp(profile.weekly_hours / opportunity.weekly_hours_required)
    if opportunity.remote:
        mobility_ease = 1.0
    else:
        denominator = max(min(profile.mobility_km, opportunity.service_radius_km), 0.001)
        mobility_ease = _clamp(1 - distance_km / denominator)
    equipment_ease = equipment_fit
    execution_score = round(100 * (
        0.30 * capital_ease
        + 0.30 * time_ease
        + 0.20 * mobility_ease
        + 0.20 * equipment_ease
    ), 2)

    score = round(
        0.30 * fit_score
        + 0.30 * economics_score
        + 0.25 * evidence_score
        + 0.10 * execution_score
        + 0.05 * opportunity.repeatability * 100,
        2,
    )
    if not isfinite(score):
        raise ValueError("assessment score is not finite")

    status = _status(gates)
    blockers = tuple(gate.reason for gate in gates if not gate.passed and gate.blocking)
    rationale.extend([
        f"fit={fit_score:.1f}/100",
        f"economics={economics_score:.1f}/100",
        f"evidence={evidence_score:.1f}/100",
        f"execution={execution_score:.1f}/100",
        f"repeatability={opportunity.repeatability:.2f}",
    ])
    if status == OpportunityStatus.RECOMMENDED:
        rationale.append("All recommendation gates pass; this is still a hypothesis to execute and observe, not an income guarantee.")
    elif status == OpportunityStatus.RESEARCH_REQUIRED:
        rationale.append("No hard blocker dominates, but at least one decision-critical uncertainty remains open.")
    else:
        rationale.append("At least one hard execution gate fails; score cannot override the blocker.")

    return Assessment(
        opportunity_id=opportunity.id,
        status=status,
        score=score,
        fit_score=fit_score,
        economics_score=economics_score,
        evidence_score=evidence_score,
        execution_score=execution_score,
        distance_km=round(distance_km, 3),
        estimated_monthly_surplus=surplus,
        estimated_payback_months=round(payback, 3) if payback is not None else None,
        gates=tuple(gates),
        blockers=blockers,
        research_questions=tuple(dict.fromkeys(research_questions)),
        rationale=tuple(rationale),
    )
