from collections import defaultdict
from pathlib import Path

import pandas as pd

from app.models.match import Match
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame
from app.models.timeline_event import TimelineEvent

from app.services.contextual_farming_service import (
    ContextualFarmingService,
)

from app.ml.disruption_features import (
    farming_disruption_features,
)


CUTOFF_MS = 10 * 60 * 1000
CUTOFF_MINUTE = 10.0

ML001_DATASET_PATH = Path(
    "artifacts/ml001/ml001_match_dataset.csv"
)

OUTPUT_DIR = Path(
    "artifacts/ml002"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "ml002b_farming_disruption_dataset.csv"
)

def _new_team_bucket():
    return {
        "kills": 0,
        "deaths": 0,
        "assists": 0,

        "objective_participations": 0,
        "dragon_participations": 0,
        "building_participations": 0,
        "turret_plate_participations": 0,

        "cs_delta": 0.0,
        "gold_delta": 0.0,
        "xp_delta": 0.0,

        "cs_observed_minutes": 0.0,
        "gold_observed_minutes": 0.0,
        "xp_observed_minutes": 0.0,

        "interval_count": 0,

        "farm_disruption_count": 0,
        "farm_relative_drop_sum": 0.0,
        "farm_max_relative_drop": 0.0,

        "farm_recovered_count": 0,
        "farm_not_recovered_count": 0,
        "farm_recovery_unavailable_count": 0,

        "farm_combat_disruption_count": 0,
    }


def _safe_rate(total, minutes):
    if minutes <= 0:
        return 0.0

    return total / minutes


def build_contextual_dataset(db):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not ML001_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"ML_001 dataset not found: "
            f"{ML001_DATASET_PATH}"
        )

    # --------------------------------------
    # SAME MATCHES USED BY ML_001
    # --------------------------------------

    base_df = pd.read_csv(
        ML001_DATASET_PATH
    )

    external_match_ids = (
        base_df["match_id"]
        .astype(str)
        .tolist()
    )

    matches = (
        db.query(Match)
        .filter(
            Match.match_id.in_(
                external_match_ids
            )
        )
        .all()
    )

    match_by_external_id = {
        match.match_id: match
        for match in matches
    }

    internal_match_ids = [
        match.id
        for match in matches
    ]

    # --------------------------------------
    # LOAD PARTICIPANTS
    # --------------------------------------

    participants = (
        db.query(MatchParticipant)
        .filter(
            MatchParticipant.match_id.in_(
                internal_match_ids
            )
        )
        .all()
    )

    participants_by_match = defaultdict(list)

    for participant in participants:
        participants_by_match[
            participant.match_id
        ].append(
            participant
        )

    # --------------------------------------
    # LOAD ONLY DATA <= MINUTE 10
    # --------------------------------------

    frames = (
        db.query(TimelineFrame)
        .filter(
            TimelineFrame.match_id.in_(
                internal_match_ids
            ),
            TimelineFrame.timestamp_ms
            <= CUTOFF_MS,
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
                internal_match_ids
            ),
            TimelineEvent.timestamp_ms
            <= CUTOFF_MS,
        )
        .order_by(
            TimelineEvent.match_id,
            TimelineEvent.timestamp_ms,
        )
        .all()
    )

    frames_by_match_participant = defaultdict(
        list
    )

    for frame in frames:

        key = (
            frame.match_id,
            frame.participant_id,
        )

        frames_by_match_participant[
            key
        ].append(frame)

    events_by_match = defaultdict(list)

    for event in events:
        events_by_match[
            event.match_id
        ].append(event)

    contextual_service = (
        ContextualFarmingService(db)
    )

    contextual_rows = []

    skipped_matches = []

    # --------------------------------------
    # BUILD TEMPORAL FEATURES
    # --------------------------------------

    for external_match_id in external_match_ids:

        match = match_by_external_id.get(
            external_match_id
        )

        if not match:
            skipped_matches.append({
                "match_id":
                    external_match_id,
                "reason":
                    "match_not_found",
            })
            continue

        match_participants = (
            participants_by_match[
                match.id
            ]
        )

        if len(match_participants) != 10:

            skipped_matches.append({
                "match_id":
                    external_match_id,
                "reason":
                    "invalid_participant_count",
            })

            continue

        teams = {
            100: _new_team_bucket(),
            200: _new_team_bucket(),
        }

        valid_match = True

        for player in match_participants:

            if player.team_id not in teams:
                valid_match = False
                break

            player_frames = (
                frames_by_match_participant[
                    (
                        match.id,
                        player.participant_id,
                    )
                ]
            )

            match_events = (
                events_by_match[
                    match.id
                ]
            )

            if len(player_frames) < 2:
                valid_match = False
                break

            intervals, skipped = (
                contextual_service
                .extract_match_intervals(
                    match=match,
                    player=player,
                    frames=player_frames,
                    events=match_events,
                )
            )

            # Absolutely no future leakage.
            intervals = [
                interval
                for interval in intervals
                if (
                    interval["end_minute"]
                    <= CUTOFF_MINUTE
                )
            ]

            farm_features = (
            farming_disruption_features(
                intervals=intervals,
                cutoff_minute=CUTOFF_MINUTE,
                )
            )

            team = teams[
                player.team_id
            ]

            team[
                "farm_disruption_count"
            ] += farm_features[
                "farm_disruption_count"
            ]

            team[
                "farm_relative_drop_sum"
            ] += (
                farm_features[
                    "farm_mean_relative_drop"
                ]
                * farm_features[
                    "farm_disruption_count"
                ]
            )

            team[
                "farm_max_relative_drop"
            ] = max(
                team[
                    "farm_max_relative_drop"
                ],
                farm_features[
                    "farm_max_relative_drop"
                ],
            )

            team[
                "farm_recovered_count"
            ] += farm_features[
                "farm_recovered_count"
            ]

            team[
                "farm_not_recovered_count"
            ] += farm_features[
                "farm_not_recovered_count"
            ]

            team[
                "farm_recovery_unavailable_count"
            ] += farm_features[
                "farm_recovery_unavailable_count"
            ]

            team[
                "farm_combat_disruption_count"
            ] += farm_features[
                "farm_combat_disruption_count"
            ]


            team = teams[
                player.team_id
            ]

            for interval in intervals:

                elapsed_minutes = (
                    interval[
                        "elapsed_seconds"
                    ]
                    / 60.0
                )

                events_data = (
                    interval.get(
                        "events"
                    )
                    or {}
                )

                team["kills"] += (
                    events_data.get(
                        "kills",
                        0,
                    )
                )

                team["deaths"] += (
                    events_data.get(
                        "deaths",
                        0,
                    )
                )

                team["assists"] += (
                    events_data.get(
                        "assists",
                        0,
                    )
                )

                team[
                    "objective_participations"
                ] += events_data.get(
                    "objective_participations",
                    0,
                )

                team[
                    "dragon_participations"
                ] += events_data.get(
                    "dragon_participations",
                    0,
                )

                team[
                    "building_participations"
                ] += events_data.get(
                    "building_participations",
                    0,
                )

                team[
                    "turret_plate_participations"
                ] += events_data.get(
                    "turret_plate_participations",
                    0,
                )

                cs_delta = interval.get(
                    "cs_delta"
                )

                if cs_delta is not None:

                    team[
                        "cs_delta"
                    ] += cs_delta

                    team[
                        "cs_observed_minutes"
                    ] += elapsed_minutes

                gold_delta = interval.get(
                    "gold_delta"
                )

                if gold_delta is not None:

                    team[
                        "gold_delta"
                    ] += gold_delta

                    team[
                        "gold_observed_minutes"
                    ] += elapsed_minutes

                xp_delta = interval.get(
                    "xp_delta"
                )

                if xp_delta is not None:

                    team[
                        "xp_delta"
                    ] += xp_delta

                    team[
                        "xp_observed_minutes"
                    ] += elapsed_minutes

                team[
                    "interval_count"
                ] += 1

        if not valid_match:

            skipped_matches.append({
                "match_id":
                    external_match_id,
                "reason":
                    "invalid_timeline",
            })

            continue

        team_100 = teams[100]
        team_200 = teams[200]

        # Average-player rates.
        team_100_cs_rate = _safe_rate(
            team_100["cs_delta"],
            team_100[
                "cs_observed_minutes"
            ],
        )

        team_200_cs_rate = _safe_rate(
            team_200["cs_delta"],
            team_200[
                "cs_observed_minutes"
            ],
        )

        team_100_gold_rate = _safe_rate(
            team_100["gold_delta"],
            team_100[
                "gold_observed_minutes"
            ],
        )

        team_200_gold_rate = _safe_rate(
            team_200["gold_delta"],
            team_200[
                "gold_observed_minutes"
            ],
        )

        team_100_xp_rate = _safe_rate(
            team_100["xp_delta"],
            team_100[
                "xp_observed_minutes"
            ],
        )

        team_200_xp_rate = _safe_rate(
            team_200["xp_delta"],
            team_200[
                "xp_observed_minutes"
            ],
        )

        team_100_farm_mean_drop = (
        team_100[
            "farm_relative_drop_sum"
        ]
        / team_100[
            "farm_disruption_count"
        ]
        if team_100[
            "farm_disruption_count"
        ] > 0
        else 0.0
        )

        team_200_farm_mean_drop = (
            team_200[
                "farm_relative_drop_sum"
            ]
            / team_200[
                "farm_disruption_count"
            ]
            if team_200[
                "farm_disruption_count"
            ] > 0
            else 0.0
        )

        

        contextual_rows.append({

            "match_id":
                external_match_id,

            # -----------------------------
            # COMBAT CONTEXT
            # -----------------------------

            "kill_difference_before_10":
                team_100["kills"]
                - team_200["kills"],

            "death_difference_before_10":
                team_100["deaths"]
                - team_200["deaths"],

            "assist_difference_before_10":
                team_100["assists"]
                - team_200["assists"],

            # -----------------------------
            # OBJECTIVE CONTEXT
            # -----------------------------

            "objective_participation_difference_before_10":
                team_100[
                    "objective_participations"
                ]
                - team_200[
                    "objective_participations"
                ],

            "dragon_participation_difference_before_10":
                team_100[
                    "dragon_participations"
                ]
                - team_200[
                    "dragon_participations"
                ],

            "building_participation_difference_before_10":
                team_100[
                    "building_participations"
                ]
                - team_200[
                    "building_participations"
                ],

            "plate_participation_difference_before_10":
                team_100[
                    "turret_plate_participations"
                ]
                - team_200[
                    "turret_plate_participations"
                ],

            # -----------------------------
            # RESOURCE ACCUMULATION
            # -----------------------------

            "cs_rate_difference_before_10":
                team_100_cs_rate
                - team_200_cs_rate,

            "gold_rate_difference_before_10":
                team_100_gold_rate
                - team_200_gold_rate,

            "xp_rate_difference_before_10":
                team_100_xp_rate
                - team_200_xp_rate,


            "farm_disruption_count_difference":
                team_100[
                    "farm_disruption_count"
                ]
                - team_200[
                    "farm_disruption_count"
                ],

            "farm_mean_drop_difference":
                team_100_farm_mean_drop
                - team_200_farm_mean_drop,

            "farm_max_drop_difference":
                team_100[
                    "farm_max_relative_drop"
                ]
                - team_200[
                    "farm_max_relative_drop"
                ],

            "farm_recovered_difference":
                team_100[
                    "farm_recovered_count"
                ]
                - team_200[
                    "farm_recovered_count"
                ],

            "farm_not_recovered_difference":
                team_100[
                    "farm_not_recovered_count"
                ]
                - team_200[
                    "farm_not_recovered_count"
                ],

            "farm_combat_disruption_difference":
                team_100[
                    "farm_combat_disruption_count"
                ]
                - team_200[
                    "farm_combat_disruption_count"
                ],
        })

    contextual_df = pd.DataFrame(
        contextual_rows
    )

    # --------------------------------------
    # MERGE WITH EXACT ML_001 DATASET
    # --------------------------------------

    merged_df = base_df.merge(
        contextual_df,
        on="match_id",
        how="inner",
        validate="one_to_one",
    )

    merged_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("ML_002 CONTEXTUAL DATASET")
    print("=========================")

    print(
        f"ML_001 matches: "
        f"{len(base_df)}"
    )

    print(
        f"ML_002 matches: "
        f"{len(merged_df)}"
    )

    print(
        f"Skipped: "
        f"{len(skipped_matches)}"
    )

    print(
        f"Missing values: "
        f"{int(merged_df.isna().sum().sum())}"
    )

    print()
    print("Contextual features:")

    contextual_columns = [
        column
        for column
        in contextual_df.columns
        if column != "match_id"
    ]

    for column in contextual_columns:
        print(
            f"  {column}"
        )

    if skipped_matches:

        print()
        print("Skipped matches:")

        for skipped in skipped_matches[
            :10
        ]:
            print(skipped)

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )

    return merged_df