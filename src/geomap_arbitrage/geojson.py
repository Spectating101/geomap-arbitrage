from __future__ import annotations

from typing import Iterable

from .models import RankedOpportunity


def ranked_to_geojson(rows: Iterable[RankedOpportunity]) -> dict:
    features = []
    for row in rows:
        opportunity = row.opportunity
        assessment = row.assessment
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [opportunity.location.lon, opportunity.location.lat],
            },
            "properties": {
                "id": opportunity.id,
                "title": opportunity.title,
                "category": opportunity.category,
                "archetype_id": opportunity.archetype_id,
                "status": assessment.status.value,
                "score": assessment.score,
                "distance_km": assessment.distance_km,
                "currency": assessment.estimated_monthly_surplus.currency,
                "surplus_low": assessment.estimated_monthly_surplus.low,
                "surplus_high": assessment.estimated_monthly_surplus.high,
                "legal_status": opportunity.legal_status.value,
                "synthetic_fixture": bool(opportunity.metadata.get("synthetic_fixture")),
            },
        })
    return {"type": "FeatureCollection", "features": features}
