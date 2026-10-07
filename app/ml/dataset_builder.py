
from collections import defaultdict
from pathlib import Path
import json

import pandas as pd

from app.models.match import Match
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame


CUTOFF_MS = 10 * 60 * 1000
MAX_FRAME_AGE_MS = 90_000
EXPECTED_PARTICIPANTS = 10

OUTPUT_DIR = Path("artifacts/ml001")
DATASET_PATH = OUTPUT_DIR / "ml001_dataset.csv"
REPORT_PATH = OUTPUT_DIR / "dataset_report.json"


def safe_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_dataset(db):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    matches = (
        db.query(Match)
        .filter(
            Match.queue_id == 420,
            Match.game_duration >= 600,
        )
        .all()
    )

    report = {
        "cutoff_minute": 10,
        "eligible_matches_found": len(matches),
        "matches_used": 0,
        "matches_skipped": {},
        "rows": 0,
        "features": [],
    }

    if not matches:
        raise ValueError(
            "No eligible ranked matches found in the database."
        )

    match_ids = [match.id for match in matches]

    participants = (
        db.query(MatchParticipant)
        .filter(MatchParticipant.match_id.in_(match_ids))
        .all()
    )

    frames = (
        db.query(TimelineFrame)
        .filter(
            TimelineFrame.match_id.in_(match_ids),
            TimelineFrame.timestamp_ms <= CUTOFF_MS,
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
        participants_by_match[participant.match_id].append(
            participant
        )

    latest_frame = {}

    for frame in frames:
        key = (frame.match_id, frame.participant_id)

        if key not in latest_frame:
            latest_frame[key] = frame

    dataset_rows = []

    for match in matches:
        match_participants = participants_by_match[match.id]

        if len(match_participants) != EXPECTED_PARTICIPANTS:
            report["matches_skipped"]["participant_count"] = (
                report["matches_skipped"].get(
                    "participant_count", 0
                ) + 1
            )
            continue

        snapshots = {}

        for participant in match_participants:
            frame = latest_frame.get(
                (match.id, participant.participant_id)
            )

            if frame is None:
                continue

            if CUTOFF_MS - frame.timestamp_ms > MAX_FRAME_AGE_MS:
                continue

            snapshots[participant.participant_id] = frame

        if len(snapshots) != EXPECTED_PARTICIPANTS:
            report["matches_skipped"]["missing_cutoff_snapshot"] = (
                report["matches_skipped"].get(
                    "missing_cutoff_snapshot", 0
                ) + 1
            )
            continue

        team_totals = defaultdict(
            lambda: {
                "gold": 0.0,
                "xp": 0.0,
                "cs": 0.0,
                "count": 0,
            }
        )

        valid_match = True

        for participant in match_participants:
            frame = snapshots[participant.participant_id]

            gold = safe_number(frame.total_gold)
            xp = safe_number(frame.xp)
            lane_cs = safe_number(frame.minions_killed)
            jungle_cs = safe_number(frame.jungle_minions_killed)

            if None in (gold, xp, lane_cs, jungle_cs):
                valid_match = False
                break

            team = team_totals[participant.team_id]

            team["gold"] += gold
            team["xp"] += xp
            team["cs"] += lane_cs + jungle_cs
            team["count"] += 1

        if not valid_match:
            report["matches_skipped"]["missing_feature_values"] = (
                report["matches_skipped"].get(
                    "missing_feature_values", 0
                ) + 1
            )
            continue

        for participant in match_participants:
            frame = snapshots[participant.participant_id]

            own_team = team_totals[participant.team_id]

            opponent_teams = [
                values
                for team_id, values in team_totals.items()
                if team_id != participant.team_id
            ]

            if len(opponent_teams) != 1:
                valid_match = False
                break

            opponent = opponent_teams[0]

            lane_cs = int(frame.minions_killed)
            jungle_cs = int(frame.jungle_minions_killed)

            row = {
                # Metadata: never use these as model features.
                "match_id": match.match_id,
                "participant_id": participant.participant_id,
                "puuid": participant.puuid,
                "game_version": match.game_version,

                # Features available at the cutoff.
                "champion_id": participant.champion_id,
                "role": participant.role,
                "lane": participant.lane,
                "level_at_10": frame.level,

                "current_gold_at_10": frame.current_gold,
                "total_gold_at_10": frame.total_gold,
                "xp_at_10": frame.xp,

                "lane_cs_at_10": lane_cs,
                "jungle_cs_at_10": jungle_cs,
                "total_cs_at_10": lane_cs + jungle_cs,

                "team_gold_at_10": own_team["gold"],
                "opponent_gold_at_10": opponent["gold"],
                "team_gold_difference_at_10": (
                    own_team["gold"] - opponent["gold"]
                ),

                "team_xp_at_10": own_team["xp"],
                "opponent_xp_at_10": opponent["xp"],
                "team_xp_difference_at_10": (
                    own_team["xp"] - opponent["xp"]
                ),

                "team_cs_at_10": own_team["cs"],
                "opponent_cs_at_10": opponent["cs"],
                "team_cs_difference_at_10": (
                    own_team["cs"] - opponent["cs"]
                ),

                # Target.
                "win": int(participant.win),
            }

            dataset_rows.append(row)

        if valid_match:
            report["matches_used"] += 1

    if not dataset_rows:
        raise ValueError(
            "No usable rows. Review cutoff snapshots and data quality."
        )

    df = pd.DataFrame(dataset_rows)

    df.to_csv(DATASET_PATH, index=False)

    report["rows"] = len(df)
    report["unique_matches"] = int(df["match_id"].nunique())
    report["wins"] = int(df["win"].sum())
    report["losses"] = int((df["win"] == 0).sum())
    report["win_rate"] = float(df["win"].mean())

    report["class_balance"] = {
        str(key): int(value)
        for key, value in df["win"].value_counts().items()
    }

    report["missing_values"] = {
        key: int(value)
        for key, value in df.isna().sum().items()
    }

    report["features"] = [
        column
        for column in df.columns
        if column not in {
            "match_id",
            "participant_id",
            "puuid",
            "game_version",
            "win",
        }
    ]

    report["dataset_path"] = str(DATASET_PATH)

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return df, report
