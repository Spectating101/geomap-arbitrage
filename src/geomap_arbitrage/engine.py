from __future__ import annotations

from datetime import date
from typing import Iterable

from .models import Opportunity, OpportunityStatus, PersonProfile, RankedOpportunity
from .scoring import assess_opportunity

_STATUS_PRIORITY = {
    OpportunityStatus.RECOMMENDED: 0,
    OpportunityStatus.RESEARCH_REQUIRED: 1,
    OpportunityStatus.BLOCKED: 2,
}


def rank_opportunities(
    profile: PersonProfile,
    opportunities: Iterable[Opportunity],
    *,
    as_of: str | date,
) -> tuple[RankedOpportunity, ...]:
    ranked = [
        RankedOpportunity(
            opportunity=opportunity,
            assessment=assess_opportunity(profile, opportunity, as_of=as_of),
        )
        for opportunity in opportunities
    ]
    ranked.sort(key=lambda row: (_STATUS_PRIORITY[row.assessment.status], -row.assessment.score, row.opportunity.id))
    return tuple(ranked)
