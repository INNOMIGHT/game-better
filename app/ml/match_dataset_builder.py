from collections import defaultdict
from pathlib import Path
import json

import pandas as pd

from app.models.match import Match
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame


CUTOFF_MS = 10 * 60 * 1000
MAX_FRAME_AGE_MS = 90_000

OUTPUT_DIR = Path("artifacts/ml001")
DATASET_PATH = OUTPUT_DIR / "ml001_match_dataset.csv"
REPORT_PATH = OUTPUT_DIR / "ml001_match_report.json"


def safe_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_match_dataset(db):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    matches = (
        db.query(Match)
        .filter(
            Match.queue_id == 420,
            Match.game_duration >= 600,
        )
        .all()
    )

    if not matches:
        raise ValueError(
            "No eligible ranked matches found."
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
            ),
            TimelineFrame.timestamp_ms
            <= CUTOFF_MS,
        )
        .order_by(
            TimelineFrame.match_id,
            TimelineFrame.participant_id,
            TimelineFrame.timestamp_ms.desc(),
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

    latest_frame = {}

    for frame in frames:

        key = (
            frame.match_id,
            frame.participant_id,
        )

        if key not in latest_frame:
            latest_frame[key] = frame

    rows = []

    skipped = defaultdict(int)

    for match in matches:

        match_participants = (
            participants_by_match[
                match.id
            ]
        )

        if len(match_participants) != 10:
            skipped[
                "participant_count"
            ] += 1
            continue

        teams = defaultdict(
            lambda: {
                "gold": 0.0,
                "xp": 0.0,
                "cs": 0.0,
                "levels": 0.0,
                "players": 0,
                "win": None,
            }
        )

        valid_match = True

        for participant in match_participants:

            frame = latest_frame.get(
                (
                    match.id,
                    participant.participant_id,
                )
            )

            if frame is None:
                valid_match = False
                break

            if (
                CUTOFF_MS
                - frame.timestamp_ms
                > MAX_FRAME_AGE_MS
            ):
                valid_match = False
                break

            gold = safe_number(
                frame.total_gold
            )

            xp = safe_number(
                frame.xp
            )

            lane_cs = safe_number(
                frame.minions_killed
            )

            jungle_cs = safe_number(
                frame.jungle_minions_killed
            )

            level = safe_number(
                frame.level
            )

            if None in (
                gold,
                xp,
                lane_cs,
                jungle_cs,
                level,
            ):
                valid_match = False
                break

            team = teams[
                participant.team_id
            ]

            team["gold"] += gold
            team["xp"] += xp
            team["cs"] += (
                lane_cs
                + jungle_cs
            )

            team["levels"] += level
            team["players"] += 1

            if team["win"] is None:
                team["win"] = bool(
                    participant.win
                )

        if not valid_match:
            skipped[
                "invalid_snapshot"
            ] += 1
            continue

        if 100 not in teams or 200 not in teams:
            skipped[
                "missing_team"
            ] += 1
            continue

        team_100 = teams[100]
        team_200 = teams[200]

        if (
            team_100["players"] != 5
            or team_200["players"] != 5
        ):
            skipped[
                "invalid_team_size"
            ] += 1
            continue

        row = {
            # Metadata
            "match_id": match.match_id,
            "game_version": match.game_version,

            # Team 100
            "team_100_gold_at_10":
                team_100["gold"],

            "team_100_xp_at_10":
                team_100["xp"],

            "team_100_cs_at_10":
                team_100["cs"],

            "team_100_level_sum_at_10":
                team_100["levels"],

            # Team 200
            "team_200_gold_at_10":
                team_200["gold"],

            "team_200_xp_at_10":
                team_200["xp"],

            "team_200_cs_at_10":
                team_200["cs"],

            "team_200_level_sum_at_10":
                team_200["levels"],

            # Differences
            "gold_difference_at_10":
                team_100["gold"]
                - team_200["gold"],

            "xp_difference_at_10":
                team_100["xp"]
                - team_200["xp"],

            "cs_difference_at_10":
                team_100["cs"]
                - team_200["cs"],

            "level_difference_at_10":
                team_100["levels"]
                - team_200["levels"],

            # Target
            "team_100_win":
                int(team_100["win"]),
        }

        rows.append(row)

    if not rows:
        raise ValueError(
            "No usable matches."
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        DATASET_PATH,
        index=False,
    )

    report = {
        "cutoff_minute": 10,
        "eligible_matches": len(matches),
        "matches_used": len(df),
        "matches_skipped": dict(skipped),

        "team_100_wins":
            int(
                df["team_100_win"].sum()
            ),

        "team_200_wins":
            int(
                (
                    df["team_100_win"] == 0
                ).sum()
            ),

        "win_rate_team_100":
            float(
                df["team_100_win"].mean()
            ),

        "missing_values": {
            column: int(value)
            for column, value
            in df.isna().sum().items()
        },

        "dataset_path":
            str(DATASET_PATH),
    }

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    return df, report