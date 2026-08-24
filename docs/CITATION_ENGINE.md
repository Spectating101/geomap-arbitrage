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

If GeoMap needs a new neutral kernel primitive merely to work, that is evidence the Citation Engine seed may still be incomplete. Conversely, if this repo can remain domain-specific while the kernel remains unchanged, the seed abstraction is doing its job.

## Persistent mode

Set:

```bash
GEOMAP_CITATION_ENGINE_STORE=/path/to/geomap.jsonl
```

The bridge uses Citation Engine's append-only `JsonlStore`. Public/result metadata only reports `memory` or `jsonl`; it does not expose the configured filesystem path.

## Version pin

`requirements.txt` pins Citation Engine to the reviewed Phase-3 semantic commit rather than moving `main`. Upgrade deliberately after conformance tests pass.
