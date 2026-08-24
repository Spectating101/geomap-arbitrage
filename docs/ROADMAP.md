# Roadmap

## v0.1 — executable seed

- [x] person/place constraint model
- [x] opportunity encyclopedia archetypes
- [x] local opportunity instance schema
- [x] evidence freshness/source-diversity gate
- [x] full-cost downside economics gate
- [x] deterministic ranking
- [x] livelihood-plan composer
- [x] GeoJSON export
- [x] Citation Engine decision/receipt/bundle integration
- [x] synthetic three-state fixture: recommended / research / blocked
- [x] persistent Citation Engine idempotence across JSONL reopen
- [x] explicit no-authority-transition recommendation boundary
- [x] native GitHub CI green on Python 3.11 and 3.13

## v0.2 — evidence adapters

Only after the seed is stable, add adapters that produce **candidate evidence**, not recommendations:

- job/service demand feeds;
- public business directories;
- public price/marketplace snapshots;
- local cost datasets;
- transport/access data;
- public regulations/licensing registers;
- procurement/tender/grant demand where appropriate.

Every adapter must preserve source locator, observation time, method, rights/terms constraints and confidence.

For internal-only development, prefer existing portfolio data sources and committed fixtures before adding new external dependencies.

## v0.3 — encyclopedia compiler

Separate reusable archetypes from local instances:

```text
pattern requirements
+ local signals
→ candidate opportunity instance
→ human/domain review
→ cited assessment
```

Add falsification prompts and evidence requests automatically from missing gates.

## v0.4 — local map surface

Build the map only after the economic model survives real data:

- status filters;
- person-profile controls;
- opportunity detail drawer;
- evidence/basis explorer;
- execution checklist;
- what-would-change-this recommendation analysis.

## v0.5 — learning loop

Execution outcomes should create new evidence rather than silently edit old claims:

- actual acquisition cost;
- actual price;
- time-to-first-sale;
- fulfillment hours;
- repeat purchase;
- failures/returns;
- permit friction;
- realized net surplus.

Use append-only revision lineage to update opportunity confidence and invalidate stale recommendations.

## Stop condition

Do not expand the project simply because another data source exists. The product is useful when it materially reduces the search cost between **a specific person/place** and **a lawful executable path to economic surplus**.
