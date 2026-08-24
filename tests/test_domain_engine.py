from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from geomap_arbitrage.catalog import load_catalog, load_profile
from geomap_arbitrage.engine import rank_opportunities
from geomap_arbitrage.geojson import ranked_to_geojson
from geomap_arbitrage.models import LegalStatus, OpportunityStatus
from geomap_arbitrage.planner import build_livelihood_plan
from geomap_arbitrage.scoring import assess_opportunity

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "examples" / "fixtures" / "profile.json"
CATALOG = ROOT / "examples" / "fixtures" / "opportunities.json"


def fixtures():
    return load_profile(PROFILE), load_catalog(CATALOG)


def test_fixture_catalog_yields_recommended_research_and_blocked_paths():
    profile, catalog = fixtures()
    ranked = rank_opportunities(profile, catalog, as_of="2026-08-24")
    assert [row.assessment.status for row in ranked] == [OpportunityStatus.RECOMMENDED, OpportunityStatus.RESEARCH_REQUIRED, OpportunityStatus.BLOCKED]
    assert ranked[0].opportunity.id == "north-harbor-catalog-cleanup"


def test_hard_capital_gate_cannot_be_rescued_by_high_score():
    profile, catalog = fixtures()
    resale = next(row for row in catalog if row.id == "north-harbor-appliance-resale")
    assessment = assess_opportunity(profile, resale, as_of="2026-08-24")
    capital = next(gate for gate in assessment.gates if gate.gate_id == "capital")
    assert capital.passed is False
    assert capital.blocking is True
    assert assessment.status == OpportunityStatus.BLOCKED


def test_unknown_legal_status_requires_research_even_with_positive_economics():
    profile, catalog = fixtures()
    bilingual = next(row for row in catalog if row.id == "north-harbor-bilingual-storefront")
    assessment = assess_opportunity(profile, bilingual, as_of="2026-08-24")
    legal = next(gate for gate in assessment.gates if gate.gate_id == "legal")
    economics = next(gate for gate in assessment.gates if gate.gate_id == "economics")
    assert legal.passed is False
    assert legal.blocking is False
    assert economics.passed is True
    assert assessment.status == OpportunityStatus.RESEARCH_REQUIRED


def test_prohibited_activity_is_blocked_without_score_override():
    profile, catalog = fixtures()
    candidate = replace(catalog[0], legal_status=LegalStatus.PROHIBITED)
    assessment = assess_opportunity(profile, candidate, as_of="2026-08-24")
    assert assessment.status == OpportunityStatus.BLOCKED
    assert any("prohibited" in blocker.lower() for blocker in assessment.blockers)


def test_stale_evidence_downgrades_recommendation_to_research_required():
    profile, catalog = fixtures()
    assessment = assess_opportunity(profile, catalog[0], as_of="2027-08-24")
    evidence = next(gate for gate in assessment.gates if gate.gate_id == "evidence")
    assert evidence.passed is False
    assert assessment.status == OpportunityStatus.RESEARCH_REQUIRED


def test_geojson_preserves_ranked_status_and_location():
    profile, catalog = fixtures()
    ranked = rank_opportunities(profile, catalog, as_of="2026-08-24")
    body = ranked_to_geojson(ranked)
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 3
    assert body["features"][0]["properties"]["status"] == "recommended"
    assert body["features"][0]["geometry"]["type"] == "Point"


def test_livelihood_plan_uses_top_executable_path_and_exposes_research_queue():
    profile, catalog = fixtures()
    ranked = rank_opportunities(profile, catalog, as_of="2026-08-24")
    plan = build_livelihood_plan(profile.id, ranked)
    assert plan.primary_opportunity_id == "north-harbor-catalog-cleanup"
    assert plan.next_actions
    assert any("bilingual" in item.lower() for item in plan.research_queue)
    assert plan.blocked_count == 1


def test_profile_receipt_snapshot_excludes_profile_identifier():
    profile, _ = fixtures()
    snapshot = profile.constraint_snapshot()
    assert "id" not in snapshot
    assert "lat" not in snapshot["location"]
    assert "lon" not in snapshot["location"]
    assert snapshot["skills"]
