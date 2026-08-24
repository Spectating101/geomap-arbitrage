from __future__ import annotations

from typing import Iterable

from .models import LivelihoodPlan, OpportunityStatus, RankedOpportunity


def build_livelihood_plan(profile_id: str, ranked: Iterable[RankedOpportunity]) -> LivelihoodPlan:
    rows = list(ranked)
    recommended = [row for row in rows if row.assessment.status == OpportunityStatus.RECOMMENDED]
    research = [row for row in rows if row.assessment.status == OpportunityStatus.RESEARCH_REQUIRED]
    blocked = [row for row in rows if row.assessment.status == OpportunityStatus.BLOCKED]

    primary = recommended[0] if recommended else None
    secondary = None
    if primary:
        secondary = next(
            (row for row in recommended[1:] if row.opportunity.category != primary.opportunity.category),
            recommended[1] if len(recommended) > 1 else None,
        )

    research_queue: list[str] = []
    for row in research[:3]:
        for question in row.assessment.research_questions:
            research_queue.append(f"{row.opportunity.title}: {question}")

    next_actions: list[str] = []
    if primary:
        next_actions.extend(primary.opportunity.execution_steps[:4])
    elif research:
        next_actions.extend(research_queue[:4])
    else:
        next_actions.append("No currently executable catalog path; collect new local demand/cost evidence and expand the opportunity encyclopedia.")

    return LivelihoodPlan(
        profile_id=profile_id,
        primary_opportunity_id=primary.opportunity.id if primary else None,
        secondary_opportunity_id=secondary.opportunity.id if secondary else None,
        research_queue=tuple(dict.fromkeys(research_queue)),
        next_actions=tuple(dict.fromkeys(next_actions)),
        blocked_count=len(blocked),
    )
