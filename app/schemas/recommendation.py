
from typing import Literal

from pydantic import BaseModel


class RecommendationEvidence(BaseModel):
    metric: str
    value: float | str
    comparison: str | None = None



class CoachingInsight(BaseModel):
    id: str

    category: Literal[
        "farming",
        "deaths",
        "consistency",
        "general",
    ]

    title: str
    observation: str

    confidence: Literal[
        "low",
        "moderate",
        "high",
    ]

    matches_analyzed: int

    role: str | None = None
    matches_with_pattern: int | None = None
    pattern_frequency_percent: float | None = None

    evidence: list[RecommendationEvidence] = []


class CoachingRecommendation(BaseModel):
    id: str

    category: Literal[
        "farming",
        "deaths",
        "consistency",
        "general",
    ]

    title: str
    observation: str
    action: str

    priority: Literal[
        "low",
        "medium",
        "high",
    ]

    confidence: Literal[
        "low",
        "moderate",
        "high",
    ]

    matches_analyzed: int

    evidence: list[RecommendationEvidence] = []


class CoachingOverview(BaseModel):
    riot_account_id: int
    total_matches_analyzed: int

    insights: list[CoachingInsight] = []

    recommendations: list[CoachingRecommendation] = []