import inspect

from app.services.contextual_farming_service import (
    ContextualFarmingService,
)

from app.services.farming_disruption_detector import (
    FarmingDisruptionDetector,
)

from app.services.economy_efficiency_detector import (
    EconomyEfficiencyDetector,
)

from app.services.economic_disruption_detector import (
    EconomicDisruptionDetector,
)

from app.services.death_pattern_detector import (
    DeathPatternDetector,
)

CLASSES = [
    ContextualFarmingService,
    FarmingDisruptionDetector,
    EconomyEfficiencyDetector,
    EconomicDisruptionDetector,
    DeathPatternDetector,
]


def main():

    print()
    print(
        "DIFFTHEORY DETECTOR CONTRACT AUDIT"
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