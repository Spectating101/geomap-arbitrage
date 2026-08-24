# Current status

**Date:** 2026-08-24  
**Stage:** v0.1 executable seed — native CI green

## What is proven

GeoMap can currently:

1. load a privacy-minimal person/place constraint profile;
2. load structured local opportunity instances and evidence signals;
3. evaluate skill, equipment, capital, time, mobility, legal, evidence and downside-economics gates;
4. classify opportunities as `recommended`, `research_required`, or `blocked` before numeric ranking;
5. rank executable paths and compose a small livelihood action plan;
6. export opportunity points as GeoJSON;
7. record each assessment through Citation Engine as evidence → assertions/citations → decision → assessment → receipt → rooted bundle;
8. persist/reopen the canonical JSONL trace idempotently;
9. prove the recommendation bundle contains no `AuthorityTransition`.

## Synthetic validation fixture

The fictional North Harbor catalog deliberately exercises three states:

```text
catalog/spreadsheet cleanup   → recommended
bilingual storefront service → research_required
used-appliance resale        → blocked
```

The blocked resale candidate still has an attractive raw score/upside range. It remains below executable candidates because startup-capital and permit gates fail. This is deliberate evidence that **gates outrank score**.

## Native validation

GeoMap PR #1 installs the pinned public Citation Engine package from GitHub and runs on Python 3.11 and 3.13.

Current matrix result on both runtimes:

```text
10 passed
cited demo smoke: pass
livelihood plan smoke: pass
GeoJSON smoke: pass
```

## Kernel feedback discovered by GeoMap

The first native run found that `JsonlStore` used raw Python equality to decide whether an existing canonical ID was being overwritten. JSON reload normalizes tuples into lists, so a semantically identical fresh object could be rejected despite having the same canonical fingerprint.

The fix was made in Citation Engine itself rather than hidden in GeoMap:

```text
store idempotence
raw Python equality
        ↓
versioned canonical-object fingerprint equality
```

Citation Engine native CI passed on Python 3.11 and 3.13 after the fix, and GeoMap was repinned to the merged fix commit.

## What is not proven

- No synthetic fixture is a real income opportunity.
- No live local market data has been integrated yet.
- Revenue/cost ranges are not forecasts.
- No automated execution exists or is implied.
- No external user validation is claimed.

The next internal engineering step is to feed the stable v0.1 engine with **existing portfolio demand/economic data** and test whether the opportunity encyclopedia can compile useful candidate instances without changing the core model.
