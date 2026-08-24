# Architecture

```text
                    OPEN ECONOMY ENCYCLOPEDIA
                  reusable opportunity archetypes
                              │
                              ▼
PERSON PROFILE ───────► LOCAL OPPORTUNITY INSTANCE ◄──── LOCAL EVIDENCE
skills                   thesis / place / costs          demand
capital                  legal status                    supply
hours                    execution playbook              price/cost
mobility                 failure modes                   regulation
assets/equipment                  │                       access
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  ▼
                         GEOMAP DOMAIN ENGINE
                    deterministic gates + scoring
                                  │
                  ┌───────────────┼────────────────┐
                  ▼               ▼                ▼
             ranked map     livelihood plan   assessment object
                                                   │
                                                   ▼
                                           CITATION ENGINE
                                     evidence / assertions / cites
                                     gate-bound domain decision
                                     receipt + rooted bundle
                                                   │
                                                   ▼
                                           inspectable output
```

## Boundary with Citation Engine

Citation Engine does **not** decide:

- whether local demand is commercially meaningful;
- which evidence classes GeoMap requires;
- whether startup capital is sufficient;
- how GeoMap scores margin/payback;
- whether a permit is needed;
- which opportunity should rank first.

GeoMap computes those domain results. Citation Engine records their basis and enforces referential integrity.

This follows the same architectural rule as other consumers: domain runtimes calculate domain truth; the shared kernel records what consequential output cites what basis.

## Why there is no authority transition

Hardware-Splicer can legitimately model an operational transition such as `power_on_authorized`. A livelihood recommendation cannot.

GeoMap therefore records:

```text
evidence
→ assertions
→ gate results
→ decision: recommended / research_required / blocked
→ assessment artifact
→ receipt
```

and stops there.

A person remains the actor who decides whether to investigate or execute the opportunity.

## Privacy boundary

The Citation Engine profile artifact stores only a constraint snapshot used in the calculation:

- locality label (exact profile coordinates are not persisted by default);
- skills;
- capital ceiling;
- time;
- mobility;
- equipment;
- languages.

The domain model intentionally contains no name, contact information, account identifiers, demographic attributes, or other unnecessary personal fields.
