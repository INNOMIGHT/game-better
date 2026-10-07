from app.analysis.performance_analyzer import (
    PerformanceAnalyzer,
)

from app.analysis.critical_moment_analyzer import (
    CriticalMomentAnalyzer,
)

from app.analysis.recommendation_engine import (
    RecommendationEngine,
)

from app.analysis.positive_moment_analyzer import (
    PositiveMomentAnalyzer,
)

from app.analysis.impact_summary import (
    ImpactSummary,
)

from app.analysis.coaching_signal_adapter import (
    CoachingSignalAdapter,
)

from app.analysis.loss_context_analyzer import (
    LossContextAnalyzer,
)

class MatchAnalysisService:

    def __init__(self):

        self.performance_analyzer = (
            PerformanceAnalyzer()
        )

        self.critical_moment_analyzer = (
            CriticalMomentAnalyzer()
        )

        self.recommendation_engine = (
            RecommendationEngine()
        )

        self.positive_moment_analyzer = (
            PositiveMomentAnalyzer()
        )

        self.signal_adapter = (
            CoachingSignalAdapter()
        )

        self.loss_context_analyzer = (
            LossContextAnalyzer()
        )

    def analyze(
        self,
        player,
        participants,
        frames,
        events,
    ):

        player_frames = [
            frame
            for frame in frames
            if (
                frame.participant_id
                == player.participant_id
            )
        ]

        performance = (
            self.performance_analyzer
            .analyze(
                player=player,
                player_frames=
                    player_frames,
                events=events,
            )
        )

        critical_analysis = (
            self.critical_moment_analyzer
            .analyze(
                player=player,
                participants=
                    participants,
                frames=frames,
                events=events,
            )
        )

        recommendations = (
            self.recommendation_engine
            .build_match_recommendations(
                critical_analysis[
                    "critical_moments"
                ]
            )
        )

        positive_analysis = (
            self.positive_moment_analyzer
            .analyze(
                player=player,
                events=events,
            )
        )

        impact_summary = (
            ImpactSummary.build(
                critical_moments=
                    critical_analysis[
                        "critical_moments"
                    ],

                positive_moments=
                    positive_analysis[
                        "positive_moments"
                    ],
            )
        )

        signals = []

        signals.extend(
            self.signal_adapter
            .from_critical_moments(
                critical_analysis[
                    "critical_moments"
                ]
            )
        )

        signals.extend(
            self.signal_adapter
            .from_positive_moments(
                positive_analysis[
                    "positive_moments"
                ]
            )
        )

        loss_context = (
            self.loss_context_analyzer
            .analyze(
                player=player,
                participants=
                    participants,
                frames=frames,

                critical_moments=
                    critical_analysis[
                        "critical_moments"
                    ],

                positive_moments=
                    positive_analysis[
                        "positive_moments"
                    ],
            )
        )

        return {
            "performance":
                performance,

            "critical_moments":
                critical_analysis[
                    "critical_moments"
                ],

            "positive_moments":
                positive_analysis[
                    "positive_moments"
                ],

            "impact_summary":
                impact_summary,

            "coaching_signals":
                signals,

            "recommendations":
                recommendations,

        }