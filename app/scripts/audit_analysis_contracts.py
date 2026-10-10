import inspect

from app.analysis.performance_analyzer import (
    PerformanceAnalyzer,
)

from app.analysis.critical_moment_analyzer import (
    CriticalMomentAnalyzer,
)

from app.analysis.positive_moment_analyzer import (
    PositiveMomentAnalyzer,
)

from app.analysis.impact_summary import (
    ImpactSummary,
)

from app.analysis.recommendation_engine import (
    RecommendationEngine,
)

from app.analysis.loss_context_analyzer import (
    LossContextAnalyzer,
)

from app.analysis.coaching_signal_adapter import (
    CoachingSignalAdapter,
)

from app.analysis.role_rank_performance_analyzer import (
    RoleRankPerformanceAnalyzer,
)


CLASSES = [
    PerformanceAnalyzer,
    CriticalMomentAnalyzer,
    PositiveMomentAnalyzer,
    ImpactSummary,
    RecommendationEngine,
    LossContextAnalyzer,
    CoachingSignalAdapter,
    RoleRankPerformanceAnalyzer,
]


def main():

    print()
    print(
        "DIFFTHEORY ANALYSIS CONTRACT AUDIT"
    )
    print(
        "=" * 70
    )

    for cls in CLASSES:

        print()
        print(
            cls.__name__
        )

        print(
            "-" * 70
        )

        for name, method in (
            inspect.getmembers(
                cls,
                predicate=inspect.isfunction,
            )
        ):

            # Ignore internal/private helpers.
            if name.startswith("_"):
                continue

            try:

                signature = (
                    inspect.signature(
                        method
                    )
                )

            except Exception:

                signature = (
                    "(signature unavailable)"
                )

            print(
                f"{name}{signature}"
            )


if __name__ == "__main__":
    main()