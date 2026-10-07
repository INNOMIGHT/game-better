from app.analysis.weakness_analyzer import (
    WeaknessAnalyzer,
)

from app.analysis.priority_analyzer import (
    PriorityAnalyzer,
)

from app.analysis.strength_analyzer import (
    StrengthAnalyzer,
)


class PlayerCoachingService:

    def __init__(
        self,
    ):

        self.weakness_analyzer = (
            WeaknessAnalyzer()
        )

        self.priority_analyzer = (
            PriorityAnalyzer()
        )

        self.strength_analyzer = (
            StrengthAnalyzer()
        )

    def analyze_recent_matches(
        self,
        match_analyses,
    ):

        weakness_analysis = (
            self.weakness_analyzer
            .analyze(
                match_analyses
            )
        )

        priority_analysis = (
            self.priority_analyzer
            .build_priorities(
                weakness_analysis=
                    weakness_analysis,
                max_priorities=5,
            )
        )

        strength_analysis = (
            self.strength_analyzer
            .analyze(
                match_analyses
            )
        )
        
        return {
            "matches_analyzed":
                len(
                    match_analyses
                ),

            "strengths":
                strength_analysis[
                    "strengths"
                ],

            "weaknesses":
                weakness_analysis[
                    "weaknesses"
                ],

            "priorities":
                priority_analysis[
                    "priorities"
                ],
        }