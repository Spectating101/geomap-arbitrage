# Citation Engine integration

GeoMap is designed as a **fresh consumer**, not a retrofit.

A cited assessment records:

```text
profile constraint artifact
opportunity artifact
source evidence artifacts
        │
        ▼
observed / hypothesis assertions
        │
        ├── typed SUPPORTS citation edges ──► source evidence
        │
        ▼
GeoMap gate results
        │
        ▼
Decision(recommended | research_required | blocked)
        │
        ▼
assessment output artifact
        │
        ▼
Receipt
        │
        ▼
citation-engine.bundle.v1
```

## Fresh-client test

This repo tests a different semantic boundary than earlier consumers:

- Cite: scholarly support assertions;
- Hardware-Splicer: operational authority after physical verification;
- GeoMap: person/place-specific economic decision support with **no authority transition**.

GeoMap required **no new Citation Engine ontology primitive**. It did, however, expose a general persistence defect in the existing kernel: after JSONL reload, JSON-normalized list payloads could be rejected as conflicting with a freshly reconstructed tuple-form object even though both had the same canonical fingerprint.

That defect was fixed upstream in Citation Engine and validated in its native Python 3.11 / 3.13 CI before GeoMap was repinned. This is exactly the intended fresh-client feedback loop: a new domain should pressure the shared invariant layer without pushing domain semantics into it.

## Persistent mode

Set:

```bash
GEOMAP_CITATION_ENGINE_STORE=/path/to/geomap.jsonl
```

The bridge uses Citation Engine's append-only `JsonlStore`. Public/result metadata only reports `memory` or `jsonl`; it does not expose the configured filesystem path.

Repeated identical assessments are idempotent across store reopen. Changed canonical semantics still fail closed.

## Authority boundary

GeoMap never calls `transition_authority()` for a recommendation. Tests inspect the exported bundle and require that no serialized object has type `AuthorityTransition`.

A `recommended` decision therefore means only:

> Under the declared profile constraints, local opportunity model, current evidence and GeoMap gates, this candidate is presently decision-ready enough to investigate/execute at the user's discretion.

It does **not** mean permission, guaranteed profit, regulatory clearance, or autonomous authorization.

## Version pin

`requirements.txt` pins Citation Engine to merged canonical-store fix commit:

```text
4c335ed14d575edf8c898f18434389dc2369a505
```

Upgrade deliberately after consumer conformance tests pass; do not track moving `main` implicitly.
