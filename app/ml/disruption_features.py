from statistics import median


CUTOFF_MINUTE = 10.0

FARM_BASELINE_WINDOW = 3
FARM_MIN_BASELINE_CS_PER_MIN = 4.0
FARM_ABSOLUTE_DROP = 2.0
FARM_RELATIVE_DROP = 0.30
FARM_RECOVERY_RATIO = 0.80


def _valid_number(value):
    if value is None:
        return False

    try:
        value = float(value)
    except (TypeError, ValueError):
        return False

    return value >= 0


def farming_disruption_features(
    intervals,
    cutoff_minute=CUTOFF_MINUTE,
):
    """
    Cutoff-safe FARM_002 feature extraction.

    Only intervals ending at or before cutoff_minute
    are allowed to participate in detection or recovery.
    """

    eligible = []

    for interval in intervals:

        if interval["end_minute"] > cutoff_minute:
            continue

        cs_per_minute = interval.get(
            "cs_per_minute"
        )

        if not _valid_number(
            cs_per_minute
        ):
            continue

        if interval.get(
            "cs_delta"
        ) is None:
            continue

        # Same exclusion used by FARM_002:
        # don't treat opening minute noise as baseline.
        if interval["end_minute"] < 2:
            continue

        eligible.append(interval)

    disruptions = []

    for index in range(
        FARM_BASELINE_WINDOW,
        len(eligible),
    ):

        current = eligible[index]

        previous = eligible[
            index - FARM_BASELINE_WINDOW:index
        ]

        baseline_values = [
            float(
                interval["cs_per_minute"]
            )
            for interval in previous
        ]

        baseline = median(
            baseline_values
        )

        observed = float(
            current["cs_per_minute"]
        )

        if (
            baseline
            < FARM_MIN_BASELINE_CS_PER_MIN
        ):
            continue

        absolute_drop = (
            baseline - observed
        )

        if absolute_drop < FARM_ABSOLUTE_DROP:
            continue

        relative_drop = (
            absolute_drop
            / baseline
        )

        if relative_drop < FARM_RELATIVE_DROP:
            continue

        recovery_status = (
            "unavailable"
        )

        # Critically: recovery may only use
        # information already available by cutoff.
        if index + 1 < len(eligible):

            next_interval = (
                eligible[index + 1]
            )

            next_rate = float(
                next_interval[
                    "cs_per_minute"
                ]
            )

            if (
                next_interval[
                    "end_minute"
                ]
                <= cutoff_minute
            ):
                recovery_status = (
                    "recovered"
                    if next_rate
                    >= (
                        baseline
                        * FARM_RECOVERY_RATIO
                    )
                    else "not_recovered"
                )

        events = (
            current.get("events")
            or {}
        )

        disruptions.append({
            "baseline_cs_per_min":
                baseline,

            "observed_cs_per_min":
                observed,

            "absolute_drop":
                absolute_drop,

            "relative_drop":
                relative_drop,

            "recovery_status":
                recovery_status,

            "combat_event":
                (
                    events.get(
                        "kills",
                        0,
                    )
                    + events.get(
                        "deaths",
                        0,
                    )
                    + events.get(
                        "assists",
                        0,
                    )
                ) > 0,
        })

    if not disruptions:

        return {
            "farm_disruption_count": 0,
            "farm_mean_relative_drop": 0.0,
            "farm_max_relative_drop": 0.0,
            "farm_recovered_count": 0,
            "farm_not_recovered_count": 0,
            "farm_recovery_unavailable_count": 0,
            "farm_combat_disruption_count": 0,
        }

    relative_drops = [
        disruption[
            "relative_drop"
        ]
        for disruption in disruptions
    ]

    return {
        "farm_disruption_count":
            len(disruptions),

        "farm_mean_relative_drop":
            sum(relative_drops)
            / len(relative_drops),

        "farm_max_relative_drop":
            max(relative_drops),

        "farm_recovered_count":
            sum(
                1
                for disruption
                in disruptions
                if disruption[
                    "recovery_status"
                ]
                == "recovered"
            ),

        "farm_not_recovered_count":
            sum(
                1
                for disruption
                in disruptions
                if disruption[
                    "recovery_status"
                ]
                == "not_recovered"
            ),

        "farm_recovery_unavailable_count":
            sum(
                1
                for disruption
                in disruptions
                if disruption[
                    "recovery_status"
                ]
                == "unavailable"
            ),

        "farm_combat_disruption_count":
            sum(
                1
                for disruption
                in disruptions
                if disruption[
                    "combat_event"
                ]
            ),
    }