from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("citation_engine")

from geomap_arbitrage.catalog import load_catalog, load_profile
from geomap_arbitrage.citation_bridge import record_assessment
from geomap_arbitrage.scoring import assess_opportunity

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "examples" / "fixtures" / "profile.json"
CATALOG = ROOT / "examples" / "fixtures" / "opportunities.json"


def _recommended():
    profile = load_profile(PROFILE)
    opportunity = load_catalog(CATALOG)[0]
    assessment = assess_opportunity(profile, opportunity, as_of="2026-08-24")
    return profile, opportunity, assessment


def test_recommendation_emits_decision_receipt_and_bundle_without_authority_transition(monkeypatch):
    monkeypatch.delenv("GEOMAP_CITATION_ENGINE_STORE", raising=False)
    profile, opportunity, assessment = _recommended()
    trace = record_assessment(profile, opportunity, assessment)
    assert trace["status"] == "recorded"
    assert trace["decisionRef"].startswith("geomap:decision:")
    assert trace["receiptRef"].startswith("geomap:receipt:")
    assert trace["bundleSchema"] == "citation-engine.bundle.v1"
    assert trace["bundleObjectCount"] >= 10
    assert trace["authorityTransition"] is None


def test_persistent_trace_is_idempotent_and_does_not_expose_store_path(monkeypatch, tmp_path):
    store_path = tmp_path / "geomap.jsonl"
    monkeypatch.setenv("GEOMAP_CITATION_ENGINE_STORE", str(store_path))
    profile, opportunity, assessment = _recommended()
    first = record_assessment(profile, opportunity, assessment)
    second = record_assessment(profile, opportunity, assessment)
    assert first["store"] == "jsonl"
    assert str(store_path) not in str(first)
    assert first["decisionDigest"] == second["decisionDigest"]
    assert first["receiptDigest"] == second["receiptDigest"]
    assert first["bundleFingerprint"] == second["bundleFingerprint"]
    assert store_path.exists()
