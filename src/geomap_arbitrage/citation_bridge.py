from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .models import Assessment, EvidenceSignal, Opportunity, PersonProfile


def _store():
    from citation_engine import JsonlStore, MemoryStore

    configured = str(os.getenv("GEOMAP_CITATION_ENGINE_STORE") or "").strip()
    if not configured:
        return MemoryStore(), "memory"
    path = Path(configured).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return JsonlStore(path), "jsonl"


def _epistemic_status(signal: EvidenceSignal):
    from citation_engine import EpistemicStatus

    method = signal.method.strip().lower()
    if method in {"verified", "audited", "deterministic"}:
        return EpistemicStatus.VERIFIED
    if method in {"modeled", "estimated", "hypothesis"}:
        return EpistemicStatus.HYPOTHESIS
    return EpistemicStatus.OBSERVED


def record_assessment(
    profile: PersonProfile,
    opportunity: Opportunity,
    assessment: Assessment,
    *,
    namespace: str = "geomap",
) -> dict[str, Any]:
    """Record a GeoMap recommendation decision in Citation Engine.

    GeoMap owns the economic model and gate semantics. Citation Engine validates and
    persists the inspectable basis graph. No AuthorityTransition is emitted: a
    livelihood recommendation is decision support, not permission to act.
    """
    from citation_engine import (
        Artifact,
        Assertion,
        Citation,
        CitationEngine,
        CitationRelation,
        Decision,
        GateResult,
        Provenance,
        Receipt,
        canonical_hash,
        export_bundle,
    )

    if assessment.opportunity_id != opportunity.id:
        raise ValueError("assessment does not belong to opportunity")

    store, store_label = _store()
    engine = CitationEngine(store)

    profile_payload = profile.constraint_snapshot()
    profile_key = canonical_hash(profile_payload)[:24]
    profile_ref = f"{namespace}:profile:{profile_key}"
    engine.record_artifact(Artifact(
        id=profile_ref,
        kind="geomap.profile_constraints",
        payload=profile_payload,
        provenance=Provenance(source="geomap-arbitrage", method="profile-constraints"),
    ))

    opportunity_payload = {
        "id": opportunity.id,
        "archetype_id": opportunity.archetype_id,
        "title": opportunity.title,
        "thesis": opportunity.thesis,
        "category": opportunity.category,
        "location": {"name": opportunity.location.name, "lat": opportunity.location.lat, "lon": opportunity.location.lon},
        "service_radius_km": opportunity.service_radius_km,
        "remote": opportunity.remote,
        "required_skills": list(opportunity.required_skills),
        "required_equipment": list(opportunity.required_equipment),
        "startup_capital": {"low": opportunity.startup_capital.low, "high": opportunity.startup_capital.high, "currency": opportunity.startup_capital.currency},
        "weekly_hours_required": opportunity.weekly_hours_required,
        "monthly_revenue": {"low": opportunity.monthly_revenue.low, "high": opportunity.monthly_revenue.high, "currency": opportunity.monthly_revenue.currency},
        "monthly_cost": {"low": opportunity.monthly_cost.low, "high": opportunity.monthly_cost.high, "currency": opportunity.monthly_cost.currency},
        "repeatability": opportunity.repeatability,
        "legal_status": opportunity.legal_status.value,
        "execution_steps": list(opportunity.execution_steps),
        "failure_modes": list(opportunity.failure_modes),
        "metadata": dict(opportunity.metadata),
    }
    opportunity_key = canonical_hash(opportunity_payload)[:24]
    opportunity_ref = f"{namespace}:opportunity:{opportunity_key}"
    engine.record_artifact(Artifact(
        id=opportunity_ref,
        kind="geomap.local_opportunity",
        payload=opportunity_payload,
        provenance=Provenance(source="geomap-arbitrage", method="opportunity-catalog"),
    ))

    evidence_refs: list[str] = []
    assertion_refs: list[str] = []
    citation_refs: list[str] = []
    assertion_refs_by_kind: dict[str, list[str]] = {}

    for signal in opportunity.evidence:
        signal_payload = {
            "signal_id": signal.id,
            "kind": signal.kind,
            "claim": signal.claim,
            "value": signal.value,
            "unit": signal.unit,
            "confidence": signal.confidence,
            "metadata": dict(signal.metadata),
        }
        signal_key = canonical_hash({
            "payload": signal_payload,
            "source": signal.source,
            "observed_at": signal.observed_at,
            "locator": signal.locator,
            "method": signal.method,
        })[:24]
        evidence_ref = f"{namespace}:evidence:{signal_key}"
        engine.record_artifact(Artifact(
            id=evidence_ref,
            kind=f"geomap.evidence.{signal.kind.strip().lower()}",
            payload=signal_payload,
            provenance=Provenance(source=signal.source, method=signal.method, locator=signal.locator, captured_at=signal.observed_at),
        ))
        evidence_refs.append(evidence_ref)

        assertion_key = canonical_hash({"opportunity_ref": opportunity_ref, "evidence_ref": evidence_ref, "kind": signal.kind, "claim": signal.claim})[:24]
        assertion = engine.record_assertion(Assertion(
            id=f"{namespace}:assertion:{assertion_key}",
            subject_ref=opportunity_ref,
            predicate=f"geomap.signal.{signal.kind.strip().lower()}",
            value={"claim": signal.claim, "value": signal.value, "unit": signal.unit},
            status=_epistemic_status(signal),
            basis_refs=(evidence_ref,),
            confidence=signal.confidence,
            produced_by="geomap-arbitrage.catalog",
        ))
        assertion_refs.append(assertion.id)
        assertion_refs_by_kind.setdefault(signal.kind.strip().lower(), []).append(assertion.id)

        citation_key = canonical_hash({"subject": assertion.id, "basis": evidence_ref})[:24]
        citation = engine.record_citation(Citation(
            id=f"{namespace}:citation:{citation_key}",
            subject_ref=assertion.id,
            basis_ref=evidence_ref,
            relation=CitationRelation.SUPPORTS,
            locator=signal.locator,
            note=signal.claim[:500],
            produced_by="geomap-arbitrage.catalog",
        ))
        citation_refs.append(citation.id)

    all_assertions = tuple(assertion_refs)
    economics_assertions = tuple(ref for kind in ("demand", "price", "cost", "economics", "supply") for ref in assertion_refs_by_kind.get(kind, ()))
    regulation_assertions = tuple(assertion_refs_by_kind.get("regulation", ()))

    gate_results: list[GateResult] = []
    for gate in assessment.gates:
        if gate.gate_id in {"skill_fit", "equipment_fit", "capital", "time", "mobility"}:
            basis = (profile_ref, opportunity_ref)
        elif gate.gate_id == "legal":
            basis = tuple(dict.fromkeys((opportunity_ref, *regulation_assertions)))
        elif gate.gate_id == "economics":
            basis = tuple(dict.fromkeys((opportunity_ref, *economics_assertions)))
        elif gate.gate_id == "evidence":
            basis = all_assertions or (opportunity_ref,)
        else:
            basis = (opportunity_ref,)
        gate_results.append(GateResult(
            gate_id=gate.gate_id,
            passed=gate.passed,
            basis_refs=basis,
            reason=f"{'blocking' if gate.blocking else 'nonblocking'}: {gate.reason}",
        ))

    decision_key = canonical_hash({"profile_ref": profile_ref, "opportunity_ref": opportunity_ref, "status": assessment.status.value, "score": assessment.score, "gates": gate_results})[:24]
    decision = engine.record_decision(Decision(
        id=f"{namespace}:decision:{decision_key}",
        subject_ref=opportunity_ref,
        outcome=assessment.status.value,
        rule_id="geomap.opportunity-assessment.v1",
        gate_results=tuple(gate_results),
        basis_refs=tuple(dict.fromkeys((profile_ref, opportunity_ref, *assertion_refs))),
    ))

    assessment_payload = assessment.as_dict()
    assessment_payload["profile_constraint_ref"] = profile_ref
    assessment_payload["opportunity_ref"] = opportunity_ref
    assessment_payload["authority_transition"] = "none_by_design"
    output_key = canonical_hash(assessment_payload)[:24]
    output_ref = f"{namespace}:assessment:{output_key}"
    engine.record_artifact(Artifact(
        id=output_ref,
        kind="geomap.assessment",
        payload=assessment_payload,
        provenance=Provenance(source="geomap-arbitrage", method="opportunity-assessment-v1", parent_refs=(decision.id,)),
    ))

    receipt_key = canonical_hash({"profile_ref": profile_ref, "opportunity_ref": opportunity_ref, "decision_ref": decision.id, "output_ref": output_ref, "citation_refs": citation_refs})[:24]
    receipt = engine.issue_receipt(Receipt(
        id=f"{namespace}:receipt:{receipt_key}",
        workflow="geomap.opportunity-assessment",
        input_refs=tuple(dict.fromkeys((profile_ref, opportunity_ref, *evidence_refs))),
        assertion_refs=tuple(assertion_refs),
        decision_refs=(decision.id,),
        output_refs=(output_ref,),
        citation_refs=tuple(citation_refs),
        metadata={"status": assessment.status.value, "score": assessment.score, "authority_transition": "none_by_design", "source_system": "geomap-arbitrage"},
    ))
    bundle = export_bundle(store, [receipt.id])

    return {
        "status": "recorded",
        "store": store_label,
        "profileRef": profile_ref,
        "opportunityRef": opportunity_ref,
        "decisionRef": decision.id,
        "decisionDigest": decision.digest,
        "assessmentRef": output_ref,
        "receiptRef": receipt.id,
        "receiptDigest": receipt.digest,
        "bundleSchema": bundle["schema"],
        "bundleFingerprint": bundle["fingerprint"],
        "bundleObjectCount": len(bundle["objects"]),
        "authorityTransition": None,
        "bundle": bundle,
    }
