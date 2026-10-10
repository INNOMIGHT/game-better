from pprint import pprint

from app.database.database import SessionLocal
from app.repositories.analytics_repository import AnalyticsRepository

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


RIOT_ACCOUNT_ID = 1
MATCH_LIMIT = 1


def summarize_output(name, value):

    print()
    print(name)
    print("=" * 70)

    print(
        f"Type: {type(value).__name__}"
    )

    if isinstance(value, list):

        print(
            f"Count: {len(value)}"
        )

        if value:

            first = value[0]

            print(
                f"First item type: "
                f"{type(first).__name__}"
            )

            if isinstance(first, dict):

                print(
                    "First item keys:"
                )

                print(
                    sorted(
                        first.keys()
                    )
                )

                print()
                print(
                    "First item:"
                )

                pprint(
                    first
                )

    elif isinstance(value, dict):

        print(
            "Top-level keys:"
        )

        print(
            sorted(
                value.keys()
            )
        )

        print()

        for key, item in value.items():

            if isinstance(
                item,
                list,
            ):

                print(
                    f"{key}: "
                    f"list[{len(item)}]"
                )

                if (
                    item
                    and isinstance(
                        item[0],
                        dict,
                    )
                ):

                    print(
                        f"  first keys: "
                        f"{sorted(item[0].keys())}"
                    )

            elif isinstance(
                item,
                dict,
            ):

                print(
                    f"{key}: dict "
                    f"{sorted(item.keys())}"
                )

            else:

                print(
                    f"{key}: {item}"
                )

    else:

        pprint(
            value
        )


def normalize_intervals(
    raw_result,
):
    """
    ContextualFarmingService.extract_match_intervals()
    currently returns a tuple.

    The first element contains the actual interval
    dictionaries used by the detectors.
    """

    if not raw_result:
        return []

    # Current service contract:
    #
    # (
    #     [interval, interval, ...],
    #     <secondary result>
    # )
    if isinstance(
        raw_result,
        tuple,
    ):

        if not raw_result:
            return []

        intervals = (
            raw_result[0]
        )

        if isinstance(
            intervals,
            list,
        ):
            return intervals

        raise TypeError(
            "Expected first tuple element "
            "from extract_match_intervals() "
            "to be a list."
        )

    # Defensive support if service later
    # returns the flat list directly.
    if isinstance(
        raw_result,
        list,
    ):
        return raw_result

    raise TypeError(
        "Unexpected result type from "
        "extract_match_intervals(): "
        f"{type(raw_result).__name__}"
    )


def main():

    db = SessionLocal()

    try:

        repository = (
            AnalyticsRepository(
                db
            )
        )

        account_result = (
            repository
            .get_riot_account(
                RIOT_ACCOUNT_ID
            )
        )

        if account_result is None:

            raise RuntimeError(
                "Riot account not found."
            )

        riot_account, _ = (
            account_result
        )

        match_results = (
            repository
            .get_player_matches(
                puuid=
                    riot_account.puuid,

                limit=
                    MATCH_LIMIT,
            )
        )

        if not match_results:

            raise RuntimeError(
                "No ranked matches found."
            )

        selected = (
            match_results[0]
        )

        match = (
            selected[
                "match"
            ]
        )

        player = (
            selected[
                "player"
            ]
        )

        all_frames = (
            repository
            .get_timeline_frames(
                [
                    match.id
                ]
            )
        )

        all_events = (
            repository
            .get_timeline_events(
                [
                    match.id
                ]
            )
        )

        player_frames = [
            frame
            for frame in all_frames
            if (
                frame.match_id
                == match.id
                and
                frame.participant_id
                == player.participant_id
            )
        ]

        events = [
            event
            for event in all_events
            if (
                event.match_id
                == match.id
            )
        ]

        print()
        print(
            "DIFFTHEORY DETECTOR OUTPUT TEST"
        )
        print(
            "=" * 70
        )

        print(
            f"Match: "
            f"{match.match_id}"
        )

        print(
            f"Player: "
            f"{player.champion_name} "
            f"{player.role}"
        )

        # ==========================================
        # INTERVALS
        # ==========================================

        contextual_service = (
            ContextualFarmingService(
                db
            )
        )

        raw_intervals = (
            contextual_service
            .extract_match_intervals(
                match=
                    match,

                player=
                    player,

                frames=
                    player_frames,

                events=
                    events,
            )
        )

        print()
        print(
            "RAW INTERVAL SHAPE"
        )
        print(
            "-" * 70
        )

        print(
            f"Outer type: "
            f"{type(raw_intervals).__name__}"
        )

        print(
            f"Outer count: "
            f"{len(raw_intervals)}"
        )

        if isinstance(
            raw_intervals,
            tuple,
        ):

            for index, item in enumerate(
                raw_intervals
            ):

                print(
                    f"Tuple item {index}: "
                    f"type={type(item).__name__}"
                )

                if isinstance(
                    item,
                    list,
                ):

                    print(
                        f"  list count="
                        f"{len(item)}"
                    )

                elif isinstance(
                    item,
                    dict,
                ):

                    print(
                        f"  keys="
                        f"{sorted(item.keys())}"
                    )

                else:

                    print(
                        f"  value="
                        f"{item}"
                    )

                intervals = (
                    normalize_intervals(
                        raw_intervals
                    )
                )

        print(
            f"Normalized interval count: "
            f"{len(intervals)}"
        )

        if intervals:

            print(
                "Interval keys:"
            )

            print(
                sorted(
                    intervals[0].keys()
                )
            )

        # ==========================================
        # FARM
        # ==========================================

        farming_result = (
            FarmingDisruptionDetector()
            .detect(
                intervals
            )
        )

        summarize_output(
            "FARMING DISRUPTION",
            farming_result,
        )

        # ==========================================
        # ECON EFFICIENCY
        # ==========================================

        economy_efficiency_result = (
            EconomyEfficiencyDetector()
            .detect(
                intervals
            )
        )

        summarize_output(
            "ECONOMY EFFICIENCY",
            economy_efficiency_result,
        )

        # ==========================================
        # ECON DISRUPTION
        # ==========================================

        economic_result = (
            EconomicDisruptionDetector()
            .detect(
                intervals
            )
        )

        summarize_output(
            "ECONOMIC DISRUPTION",
            economic_result,
        )

        # ==========================================
        # DEATH PATTERNS
        # ==========================================

        death_result = (
            DeathPatternDetector()
            .detect(
                intervals
            )
        )

        summarize_output(
            "DEATH PATTERNS",
            death_result,
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()