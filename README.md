# GeoMap Arbitrage

**Open-source local economic opportunity intelligence.**

GeoMap Arbitrage maps lawful, executable economic mismatches to the people and places that can exploit them: unmet local demand, skill scarcity, geographic price spreads, underused assets, logistics gaps, remote-income/local-cost advantages, and related forms of real-world arbitrage.

The core question is deliberately practical:

> Given this person, in this place, with these skills, resources, constraints, and time horizon: what can they actually do to build income, why should it work, what would it cost, and what evidence supports the recommendation?

This is **not** a trading bot and not a promise of income. “Arbitrage” here means a lawful mismatch in value, capability, access, geography, timing, or utilization that may be executable after full costs and constraints are considered.

## Why this exists

Most economic advice is either too generic (“learn a skill”, “start a business”) or too secretive (“alpha”). GeoMap treats opportunity knowledge as a mapable, inspectable commons:

```text
person constraints
+ place
+ opportunity archetype
+ local evidence
+ full-cost economics
+ legal / execution gates
        ↓
ranked livelihood paths
+ research gaps
+ execution playbook
+ evidence receipt
```

The long-term idea is an **open-source economy encyclopedia**: reusable opportunity archetypes plus local evidence instances, so a person can ask what is actually plausible *here*, *for them*, instead of receiving generic entrepreneurship content.

## v0.1 architecture

GeoMap owns the domain semantics:

- person/place fit;
- opportunity archetypes;
- startup capital, time and mobility constraints;
- conservative revenue/cost ranges;
- evidence freshness and source diversity;
- legal/regulatory readiness;
- ranking and livelihood planning.

[`Spectating101/citation-engine`](https://github.com/Spectating101/citation-engine) owns the neutral evidence substrate:

- canonical evidence objects;
- provenance;
- assertions and typed citation edges;
- inspectable gate/decision basis;
- reproducible receipts;
- rooted portable bundles.

A GeoMap recommendation deliberately creates **no `AuthorityTransition`**. The system can say “current evidence supports trying/researching this path”; it does not grant permission, guarantee profit, or replace local legal/professional judgment.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
pytest -q
```

Run the synthetic demo:

```bash
geomap demo
geomap demo --json
geomap plan --json
geomap geojson --output /tmp/geomap-demo.geojson
```

`geomap demo` is cited by default. Each assessed opportunity produces a Citation Engine decision, receipt, and `citation-engine.bundle.v1` fingerprint. Use `--uncited` only for domain debugging.

### Persistent canonical trace

```bash
GEOMAP_CITATION_ENGINE_STORE=/tmp/geomap.jsonl geomap demo --json
```

Trace output reveals only `store: "jsonl"`; the server/local filesystem path is not exposed in the recommendation object.

## Status semantics

- `recommended` — every current recommendation gate passes.
- `research_required` — no hard blocker dominates, but a decision-critical uncertainty remains (for example regulation, evidence coverage, equipment, learnable skill, or downside economics).
- `blocked` — at least one hard execution gate fails (for example prohibited activity, insufficient minimum capital, unreachable location/time constraint, or negative optimistic economics).

The numeric score **never overrides gates**.

## Current fixture

`examples/fixtures/` contains a fictional place called **North Harbor** and three synthetic opportunities. It exists solely to test the architecture. It must not be interpreted as current market research or a real income recommendation.

## Repository map

```text
src/geomap_arbitrage/
  models.py             domain objects
  geometry.py           geographic distance
  scoring.py            deterministic gates + ranking score
  engine.py             catalog ranking
  planner.py            small livelihood-plan composer
  geojson.py            map interchange surface
  citation_bridge.py    Citation Engine consumer boundary
  catalog.py            JSON loaders
  cli.py                local command surface

encyclopedia/
  patterns.json         reusable opportunity archetypes

examples/fixtures/
  profile.json
  opportunities.json

docs/
  OPEN_SOURCE_ECONOMY.md
  OPPORTUNITY_MODEL.md
  ARCHITECTURE.md
  CITATION_ENGINE.md
  ROADMAP.md
  SAFETY_AND_BOUNDARIES.md
```

## Development doctrine

1. **Evidence before recommendation.** A good story is not a local opportunity.
2. **Full cost before spread.** Transport, defects, acquisition, time, regulation, returns, and working capital belong in the economics.
3. **Gates before score.** High upside cannot rescue a hard blocker.
4. **Local specificity.** Generic opportunity archetypes become actionable only after place-specific evidence.
5. **Person specificity.** The same local opportunity can be excellent for one profile and unusable for another.
6. **No silent certainty promotion.** Estimated/modelled signals stay labelled as such.
7. **Open playbook, private person.** The opportunity encyclopedia can be public; personal constraint data should be minimized.

See `docs/ROADMAP.md` for the next build sequence.
