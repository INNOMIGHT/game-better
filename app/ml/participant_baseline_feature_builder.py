from pathlib import Path

import pandas as pd

from app.models.match import Match
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame


INPUT_DIR = Path(
    "artifacts/rank_baseline"
)

OUTPUT_DIR = Path(
    "artifacts/rank_baseline/features"
)

CUTOFF_MS = (
    10
    * 60
    * 1000
)


class ParticipantBaselineFeatureBuilder:

    def __init__(
        self,
        db,
    ):
        self.db = db

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _total_cs(
        frame,
    ):

        if frame is None:
            return None

        return (
            (frame.minions_killed or 0)
            +
            (
                frame.jungle_minions_killed
                or 0
            )
        )

    @staticmethod
    def _latest_frame_before(
        frames,
        timestamp_ms,
    ):

        latest = None

        for frame in frames:

            if (
                frame.timestamp_ms
                > timestamp_ms
            ):
                break

            latest = frame

        return latest

    @staticmethod
    def _final_frame(
        frames,
    ):

        if not frames:
            return None

        return frames[-1]

    # ==================================================
    # DATABASE LOOKUPS
    # ==================================================

    def _get_match(
        self,
        riot_match_id,
    ):

        return (
            self.db
            .query(
                Match
            )
            .filter(
                Match.match_id
                == riot_match_id
            )
            .first()
        )

    def _get_participant(
        self,
        internal_match_id,
        participant_id,
    ):

        return (
            self.db
            .query(
                MatchParticipant
            )
            .filter(
                MatchParticipant.match_id
                == internal_match_id,

                MatchParticipant.participant_id
                == participant_id,
            )
            .first()
        )

    def _get_frames(
        self,
        internal_match_id,
        participant_id,
    ):

        return (
            self.db
            .query(
                TimelineFrame
            )
            .filter(
                TimelineFrame.match_id
                == internal_match_id,

                TimelineFrame.participant_id
                == participant_id,
            )
            .order_by(
                TimelineFrame.timestamp_ms
            )
            .all()
        )

    # ==================================================
    # SINGLE FEATURE ROW
    # ==================================================

    def _build_row(
        self,
        sample,
    ):

        riot_match_id = sample[
            "match_id"
        ]

        participant_id = int(
            sample[
                "participant_id"
            ]
        )

        # ----------------------------------
        # Find canonical Match row
        # ----------------------------------

        match = self._get_match(
            riot_match_id
        )

        if match is None:

            print(
                f"Missing Match: "
                f"{riot_match_id}"
            )

            return None

        # ----------------------------------
        # IMPORTANT:
        # related tables use DB Match.id
        # ----------------------------------

        internal_match_id = (
            match.id
        )

        participant = (
            self._get_participant(
                internal_match_id=
                    internal_match_id,

                participant_id=
                    participant_id,
            )
        )

        if participant is None:

            print(
                f"Missing participant: "
                f"{riot_match_id} "
                f"participant="
                f"{participant_id}"
            )

            return None

        frames = (
            self._get_frames(
                internal_match_id=
                    internal_match_id,

                participant_id=
                    participant_id,
            )
        )

        if not frames:

            print(
                f"Missing frames: "
                f"{riot_match_id} "
                f"participant="
                f"{participant_id}"
            )

            return None

        # ----------------------------------
        # Minute 10 snapshot
        # ----------------------------------

        frame_10 = (
            self._latest_frame_before(
                frames,
                CUTOFF_MS,
            )
        )

        final_frame = (
            self._final_frame(
                frames
            )
        )

        if frame_10 is None:

            print(
                f"No minute-10 frame: "
                f"{riot_match_id}"
            )

            return None

        if final_frame is None:

            return None

        frame_10_age = (
            CUTOFF_MS
            - frame_10.timestamp_ms
        )

        # Don't accept a stale frame from
        # several minutes earlier.
        if (
            frame_10_age
            > 90_000
        ):

            print(
                f"Minute-10 frame too old: "
                f"{riot_match_id} "
                f"age_ms={frame_10_age}"
            )

            return None

        cs_10 = (
            self._total_cs(
                frame_10
            )
        )

        final_cs = (
            self._total_cs(
                final_frame
            )
        )

        game_minutes = (
            final_frame.timestamp_ms
            / 60_000
        )

        if game_minutes <= 0:
            return None

        # ----------------------------------
        # Participant values
        # ----------------------------------

        kills = (
            getattr(
                participant,
                "kills",
                0,
            )
            or 0
        )

        deaths = (
            getattr(
                participant,
                "deaths",
                0,
            )
            or 0
        )

        assists = (
            getattr(
                participant,
                "assists",
                0,
            )
            or 0
        )

        kda = (
            (
                kills
                + assists
            )
            / max(
                deaths,
                1,
            )
        )

        # Prefer final timeline gold.
        final_gold = (
            final_frame.total_gold
            or getattr(
                participant,
                "gold_earned",
                0,
            )
            or getattr(
                participant,
                "total_gold",
                0,
            )
            or 0
        )

        role = (
            sample.get(
                "role"
            )
            or getattr(
                participant,
                "role",
                None,
            )
        )

        champion = (
            getattr(
                participant,
                "champion_name",
                None,
            )
            or sample.get(
                "champion"
            )
        )

        # ==================================================
        # RESULT
        # ==================================================

        return {
            # ----------------------------------
            # Identity / metadata
            # ----------------------------------

            "match_id":
                riot_match_id,

            "internal_match_id":
                internal_match_id,

            "puuid":
                sample[
                    "puuid"
                ],

            "participant_id":
                participant_id,

            "rank_bucket":
                sample[
                    "rank_bucket"
                ],

            "tier":
                sample[
                    "tier"
                ],

            "division":
                sample[
                    "division"
                ],

            "league_points":
                sample[
                    "league_points"
                ],

            "role":
                role,

            "champion":
                champion,

            "game_version":
                sample.get(
                    "game_version"
                ),

            "win":
                int(
                    bool(
                        participant.win
                    )
                ),

            # ==================================
            # MINUTE 10
            # ==================================

            "gold_at_10":
                (
                    frame_10.total_gold
                    or 0
                ),

            "xp_at_10":
                (
                    frame_10.xp
                    or 0
                ),

            "cs_at_10":
                cs_10,

            "level_at_10":
                (
                    frame_10.level
                    or 0
                ),

            "cs_per_min_at_10":
                (
                    cs_10
                    / 10.0
                ),

            "gold_per_min_at_10":
                (
                    (
                        frame_10.total_gold
                        or 0
                    )
                    / 10.0
                ),

            "xp_per_min_at_10":
                (
                    (
                        frame_10.xp
                        or 0
                    )
                    / 10.0
                ),

            # ==================================
            # FULL MATCH
            # ==================================

            "game_minutes":
                round(
                    game_minutes,
                    2,
                ),

            "final_cs":
                final_cs,

            "cs_per_min":
                (
                    final_cs
                    / game_minutes
                ),

            "final_gold":
                final_gold,

            "gold_per_min":
                (
                    final_gold
                    / game_minutes
                ),

            # ==================================
            # COMBAT
            # ==================================

            "kills":
                kills,

            "deaths":
                deaths,

            "assists":
                assists,

            "kda":
                round(
                    kda,
                    3,
                ),
        }

    # ==================================================
    # FULL DATASET BUILD
    # ==================================================

    def build(
        self,
        tier,
    ):

        tier = tier.upper()

        input_path = (
            INPUT_DIR
            / f"{tier}_rank_sample_index.csv"
        )

        if not input_path.exists():

            raise FileNotFoundError(
                "Rank sample index "
                f"not found: {input_path}"
            )

        samples = (
            pd.read_csv(
                input_path
            )
        )

        rows = []

        skipped = 0

        for index, sample in (
            samples.iterrows()
        ):

            row = (
                self._build_row(
                    sample
                )
            )

            if row is None:

                skipped += 1

                continue

            rows.append(
                row
            )

        df = (
            pd.DataFrame(
                rows
            )
        )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            OUTPUT_DIR
            / (
                f"{tier}_"
                "participant_features.csv"
            )
        )

        df.to_csv(
            output_path,
            index=False,
        )

        print()
        print(
            f"{tier} PARTICIPANT "
            "BASELINE FEATURES"
        )
        print(
            "=" * 40
        )

        print(
            f"Input samples: "
            f"{len(samples)}"
        )

        print(
            f"Feature rows: "
            f"{len(df)}"
        )

        print(
            f"Skipped: "
            f"{skipped}"
        )

        if not df.empty:

            print()
            print(
                "ROLE COUNTS"
            )

            print(
                df[
                    "role"
                ].value_counts(
                    dropna=False
                )
            )

            print()
            print(
                "FEATURE SUMMARY"
            )

            summary_columns = [
                "gold_at_10",
                "xp_at_10",
                "cs_at_10",
                "level_at_10",
                "cs_per_min",
                "gold_per_min",
                "kills",
                "deaths",
                "assists",
                "kda",
            ]

            print(
                df[
                    summary_columns
                ].describe()
            )

        print()
        print(
            f"Saved: "
            f"{output_path}"
        )

        return df