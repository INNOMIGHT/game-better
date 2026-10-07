from collections import defaultdict
from pathlib import Path
from statistics import median

import pandas as pd

from app.models.match import Match
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame
from app.models.timeline_event import TimelineEvent

from app.services.contextual_farming_service import (
    ContextualFarmingService,
)


OUTPUT_DIR = Path(
    "artifacts/ml_farm"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "farm_recovery_dataset.csv"
)


# FARM disruption definition
BASELINE_WINDOW = 3

MIN_BASELINE_CS_PER_MIN = 4.0

MIN_ABSOLUTE_DROP = 2.0

MIN_RELATIVE_DROP = 0.30


# Recovery definition for this ML experiment.
#
# We look at the next 3 valid intervals.
# At least 2 must exist.
#
# Recovery = median future CS rate
# reaches at least 80% of the
# pre-disruption baseline.
RECOVERY_WINDOW = 3

MIN_RECOVERY_OBSERVATIONS = 2

RECOVERY_RATIO = 0.80


def _valid_number(value):

    if value is None:
        return False

    try:
        value = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return False

    return value >= 0


def _rate(
    value,
    elapsed_seconds,
):

    if (
        value is None
        or elapsed_seconds is None
        or elapsed_seconds <= 0
    ):
        return None

    minutes = (
        elapsed_seconds
        / 60.0
    )

    if minutes <= 0:
        return None

    return (
        value
        / minutes
    )


def _sum_events(
    intervals,
    key,
):

    return sum(
        (
            interval.get(
                "events"
            )
            or {}
        ).get(
            key,
            0,
        )
        for interval in intervals
    )


def _build_disruption_rows(
    match,
    player,
    intervals,
):

    # --------------------------------------
    # Keep only intervals with valid CS
    # --------------------------------------

    eligible = []

    for interval in intervals:

        if (
            interval["end_minute"]
            < 2.0
        ):
            continue

        if not _valid_number(
            interval.get(
                "cs_per_minute"
            )
        ):
            continue

        eligible.append(
            interval
        )

    rows = []

    for index in range(
        BASELINE_WINDOW,
        len(eligible),
    ):

        current = eligible[
            index
        ]

        previous = eligible[
            index - BASELINE_WINDOW:index
        ]

        previous_cs_rates = [
            float(
                interval[
                    "cs_per_minute"
                ]
            )
            for interval
            in previous
        ]

        baseline_cs = median(
            previous_cs_rates
        )

        observed_cs = float(
            current[
                "cs_per_minute"
            ]
        )

        # ----------------------------------
        # FARM disruption detection
        # ----------------------------------

        if (
            baseline_cs
            < MIN_BASELINE_CS_PER_MIN
        ):
            continue

        absolute_drop = (
            baseline_cs
            - observed_cs
        )

        if (
            absolute_drop
            < MIN_ABSOLUTE_DROP
        ):
            continue

        relative_drop = (
            absolute_drop
            / baseline_cs
        )

        if (
            relative_drop
            < MIN_RELATIVE_DROP
        ):
            continue

        # ----------------------------------
        # FUTURE TARGET WINDOW
        #
        # FUTURE INFORMATION IS USED ONLY
        # FOR THE TARGET.
        # ----------------------------------

        future = eligible[
            index + 1:
            index + 1 + RECOVERY_WINDOW
        ]

        if (
            len(future)
            < MIN_RECOVERY_OBSERVATIONS
        ):
            # We cannot confidently label
            # recovery near the end of game.
            continue

        future_rates = [
            float(
                interval[
                    "cs_per_minute"
                ]
            )
            for interval
            in future
        ]

        future_median_cs = median(
            future_rates
        )

        recovery_threshold = (
            baseline_cs
            * RECOVERY_RATIO
        )

        recovered = int(
            future_median_cs
            >= recovery_threshold
        )

        # ----------------------------------
        # CURRENT INTERVAL FEATURES
        # ----------------------------------

        elapsed_seconds = (
            current[
                "elapsed_seconds"
            ]
        )

        current_gold_rate = _rate(
            current.get(
                "gold_delta"
            ),
            elapsed_seconds,
        )

        current_xp_rate = _rate(
            current.get(
                "xp_delta"
            ),
            elapsed_seconds,
        )

        # ----------------------------------
        # PRE-DISRUPTION RESOURCE CONTEXT
        # ----------------------------------

        previous_gold_rates = []

        previous_xp_rates = []

        for interval in previous:

            interval_seconds = (
                interval[
                    "elapsed_seconds"
                ]
            )

            gold_rate = _rate(
                interval.get(
                    "gold_delta"
                ),
                interval_seconds,
            )

            xp_rate = _rate(
                interval.get(
                    "xp_delta"
                ),
                interval_seconds,
            )

            if gold_rate is not None:
                previous_gold_rates.append(
                    gold_rate
                )

            if xp_rate is not None:
                previous_xp_rates.append(
                    xp_rate
                )

        baseline_gold_rate = (
            median(
                previous_gold_rates
            )
            if previous_gold_rates
            else 0.0
        )

        baseline_xp_rate = (
            median(
                previous_xp_rates
            )
            if previous_xp_rates
            else 0.0
        )

        current_gold_rate = (
            current_gold_rate
            if current_gold_rate
            is not None
            else 0.0
        )

        current_xp_rate = (
            current_xp_rate
            if current_xp_rate
            is not None
            else 0.0
        )

        current_events = (
            current.get(
                "events"
            )
            or {}
        )

        # ----------------------------------
        # CREATE ONE ML SAMPLE
        # ----------------------------------

        rows.append({

            # Metadata.
            # Do NOT train on these.
            "match_id":
                match.match_id,

            "participant_id":
                player.participant_id,

            "puuid":
                player.puuid,

            "champion":
                player.champion_name,

            "role":
                player.role,

            "game_version":
                match.game_version,

            # --------------------------------
            # Disruption timing/context
            # --------------------------------

            "disruption_minute":
                current[
                    "end_minute"
                ],

            "interval_seconds":
                elapsed_seconds,

            "level_at_disruption":
                (
                    current.get(
                        "level_end"
                    )
                    or 0
                ),

            # --------------------------------
            # FARM disruption severity
            # --------------------------------

            "baseline_cs_per_min":
                baseline_cs,

            "observed_cs_per_min":
                observed_cs,

            "absolute_cs_drop":
                absolute_drop,

            "relative_cs_drop":
                relative_drop,

            # --------------------------------
            # Resource context
            # --------------------------------

            "baseline_gold_per_min":
                baseline_gold_rate,

            "current_gold_per_min":
                current_gold_rate,

            "gold_rate_change":
                (
                    current_gold_rate
                    - baseline_gold_rate
                ),

            "baseline_xp_per_min":
                baseline_xp_rate,

            "current_xp_per_min":
                current_xp_rate,

            "xp_rate_change":
                (
                    current_xp_rate
                    - baseline_xp_rate
                ),

            # --------------------------------
            # Current event context
            # --------------------------------

            "kills_during_disruption":
                current_events.get(
                    "kills",
                    0,
                ),

            "deaths_during_disruption":
                current_events.get(
                    "deaths",
                    0,
                ),

            "assists_during_disruption":
                current_events.get(
                    "assists",
                    0,
                ),

            "objectives_during_disruption":
                current_events.get(
                    "objective_participations",
                    0,
                ),

            # --------------------------------
            # Recent context before disruption
            # --------------------------------

            "recent_kills":
                _sum_events(
                    previous,
                    "kills",
                ),

            "recent_deaths":
                _sum_events(
                    previous,
                    "deaths",
                ),

            "recent_assists":
                _sum_events(
                    previous,
                    "assists",
                ),

            "recent_objectives":
                _sum_events(
                    previous,
                    "objective_participations",
                ),

            # --------------------------------
            # TARGET
            #
            # NEVER use the fields below
            # as input features.
            # --------------------------------

            "recovered":
                recovered,

            # Keep this for validation /
            # analysis only.
            "future_median_cs_per_min":
                future_median_cs,

            "recovery_threshold":
                recovery_threshold,
        })

    return rows


def build_farm_recovery_dataset(
    db,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------
    # USE ALL STORED RANKED SOLO MATCHES
    # --------------------------------------

    matches = (
        db.query(Match)
        .filter(
            Match.queue_id == 420
        )
        .all()
    )

    if not matches:
        raise RuntimeError(
            "No ranked Solo/Duo matches found."
        )

    match_ids = [
        match.id
        for match in matches
    ]

    participants = (
        db.query(MatchParticipant)
        .filter(
            MatchParticipant.match_id.in_(
                match_ids
            )
        )
        .all()
    )

    frames = (
        db.query(TimelineFrame)
        .filter(
            TimelineFrame.match_id.in_(
                match_ids
            )
        )
        .order_by(
            TimelineFrame.match_id,
            TimelineFrame.participant_id,
            TimelineFrame.timestamp_ms,
        )
        .all()
    )

    events = (
        db.query(TimelineEvent)
        .filter(
            TimelineEvent.match_id.in_(
                match_ids
            )
        )
        .order_by(
            TimelineEvent.match_id,
            TimelineEvent.timestamp_ms,
        )
        .all()
    )

    participants_by_match = (
        defaultdict(list)
    )

    for participant in participants:

        participants_by_match[
            participant.match_id
        ].append(
            participant
        )

    frames_by_match_participant = (
        defaultdict(list)
    )

    for frame in frames:

        frames_by_match_participant[
            (
                frame.match_id,
                frame.participant_id,
            )
        ].append(
            frame
        )

    events_by_match = (
        defaultdict(list)
    )

    for event in events:

        events_by_match[
            event.match_id
        ].append(
            event
        )

    contextual_service = (
        ContextualFarmingService(db)
    )

    rows = []

    matches_used = 0

    participants_used = 0

    for match in matches:

        match_participants = (
            participants_by_match[
                match.id
            ]
        )

        if len(
            match_participants
        ) != 10:
            continue

        match_has_sample = False

        for player in match_participants:

            player_frames = (
                frames_by_match_participant[
                    (
                        match.id,
                        player.participant_id,
                    )
                ]
            )

            if len(player_frames) < 5:
                continue

            intervals, skipped = (
                contextual_service
                .extract_match_intervals(
                    match=match,
                    player=player,
                    frames=player_frames,
                    events=events_by_match[
                        match.id
                    ],
                )
            )

            player_rows = (
                _build_disruption_rows(
                    match=match,
                    player=player,
                    intervals=intervals,
                )
            )

            if player_rows:

                participants_used += 1

                match_has_sample = True

                rows.extend(
                    player_rows
                )

        if match_has_sample:
            matches_used += 1

    df = pd.DataFrame(
        rows
    )

    if df.empty:

        raise RuntimeError(
            "No farming disruption "
            "samples were generated."
        )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        "ML_FARM_001 DATASET REPORT"
    )
    print(
        "=========================="
    )

    print(
        f"Stored ranked matches: "
        f"{len(matches)}"
    )

    print(
        f"Matches with disruptions: "
        f"{matches_used}"
    )

    print(
        f"Participants with disruptions: "
        f"{participants_used}"
    )

    print(
        f"Total disruption samples: "
        f"{len(df)}"
    )

    positives = int(
        df["recovered"].sum()
    )

    negatives = (
        len(df)
        - positives
    )

    print(
        f"Recovered: "
        f"{positives}"
    )

    print(
        f"Not recovered: "
        f"{negatives}"
    )

    print(
        f"Recovery rate: "
        f"{df['recovered'].mean():.3f}"
    )

    print(
        f"Unique matches: "
        f"{df['match_id'].nunique()}"
    )

    print(
        f"Missing values: "
        f"{int(df.isna().sum().sum())}"
    )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )

    return df