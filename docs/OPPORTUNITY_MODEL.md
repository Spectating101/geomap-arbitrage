# Opportunity model

## Opportunity = executable mismatch

GeoMap uses “arbitrage” broadly: a lawful mismatch in value, capability, access, geography, time, information, or utilization that may produce positive surplus after full cost.

An opportunity instance contains:

- `archetype_id` — reusable pattern from the encyclopedia;
- `thesis` — why the mismatch may exist;
- geographic point + service radius or `remote=true`;
- required/helpful skills and equipment;
- startup-capital range;
- weekly time requirement;
- monthly revenue and cost ranges;
- repeatability estimate;
- legal status;
- required evidence classes;
- execution steps and failure modes;
- evidence signals with source, date, confidence, method and locator.

## Evidence classes

The model is intentionally open-ended, but common classes include:

- `demand`
- `supply`
- `price`
- `cost`
- `economics`
- `asset`
- `access`
- `regulation`
- `capability`

A catalog entry declares which classes are mandatory before it can become `recommended`.

## Gate model

Current v0.1 gates:

1. required skill fit;
2. equipment fit;
3. startup-capital affordability;
4. weekly time capacity;
5. mobility / geographic reach;
6. legal/regulatory readiness;
7. evidence freshness, coverage, diversity and confidence;
8. downside economics.

Failed gates are either:

- **blocking** — current profile/opportunity should not be recommended;
- **nonblocking** — opportunity remains investigable but not decision-ready.

## Economics

The engine uses ranges rather than one forecast.

```text
conservative surplus = revenue.low - cost.high
optimistic surplus   = revenue.high - cost.low
```

- optimistic surplus <= 0 → blocked;
- optimistic positive but conservative <= 0 → research required;
- conservative positive → economics gate passes.

This is still only a model. Real execution should feed observed results back into the catalog.

## Score

The score combines:

- person/opportunity fit;
- economics;
- evidence quality;
- execution ease;
- repeatability.

It ranks candidates **after** the gate semantics are known. Status sorting precedes score sorting, so a blocked opportunity never outranks an executable one simply because its upside looks larger.
