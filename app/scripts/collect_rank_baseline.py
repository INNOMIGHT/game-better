from pathlib import Path

import pandas as pd

from app.database.database import (
    SessionLocal,
)

from app.riot.client import (
    RiotClient,
)

from app.repositories.match_repository import (
    MatchRepository,
)

from app.services.rank_sample_service import (
    RankSampleService,
)

from app.services.rank_baseline_collection_service import (
    RankBaselineCollectionService,
)


# ==================================================
# CONFIG
# ==================================================

PLATFORM = "EUW1"

REGION = "EUROPE"

TIER = "DIAMOND"

TARGET_PLAYERS = 60

MATCHES_PER_PLAYER = 5

TARGET_MATCHES = 200


# ==================================================
# OUTPUT
# ==================================================

OUTPUT_DIR = Path(
    "artifacts/rank_baseline"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / f"{TIER}_rank_sample_index.csv"
)


def main():

    db = SessionLocal()

    riot_client = RiotClient()

    try:

        # ==========================================
        # SERVICES
        # ==========================================

        sample_service = (
            RankSampleService(
                riot_client
            )
        )

        repository = (
            MatchRepository(
                db
            )
        )

        collector = (
            RankBaselineCollectionService(
                db=
                    db,

                riot_client=
                    riot_client,

                match_repository=
                    repository,
            )
        )

        # ==========================================
        # SAMPLE RANKED PLAYERS
        # ==========================================

        print()

        print(
            f"Finding "
            f"{TIER} players..."
        )

        if (
            TIER
            == "MASTER_PLUS"
        ):

            players = (
                sample_service
                .collect_master_plus_players(
                    platform=
                        PLATFORM,

                    target_players=
                        TARGET_PLAYERS,
                )
            )

        else:

            players = (
                sample_service
                .collect_standard_tier_players(
                    platform=
                        PLATFORM,

                    tier=
                        TIER,

                    target_players=
                        TARGET_PLAYERS,
                )
            )

        print(
            f"Ranked players found: "
            f"{len(players)}"
        )

        if not players:

            raise RuntimeError(
                f"No ranked players "
                f"found for "
                f"{TIER}."
            )

        # ==========================================
        # COLLECT MATCHES
        # ==========================================

        print()

        print(
            "Collecting recent "
            "ranked matches..."
        )

        result = (
            collector
            .collect_for_players(
                players=
                    players,

                region=
                    REGION,

                expected_platform=
                    PLATFORM,

                matches_per_player=
                    MATCHES_PER_PLAYER,

                target_unique_matches=
                    TARGET_MATCHES,
            )
        )

        rows = (
            result[
                "rows"
            ]
        )

        # ==========================================
        # SAVE INDEX
        # ==========================================

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        df = pd.DataFrame(
            rows
        )

        df.to_csv(
            OUTPUT_PATH,
            index=False,
        )

        # ==========================================
        # REPORT
        # ==========================================

        print()

        print(
            f"{TIER} "
            f"BASELINE COLLECTION"
        )

        print(
            "=" * 32
        )

        print(
            f"Players sampled: "
            f"{len(players)}"
        )

        print(
            f"Unique matches: "
            f"{result['unique_matches']}"
        )

        print(
            f"Rank-labelled rows: "
            f"{len(rows)}"
        )

        print(
            f"New matches saved: "
            f"{result['new_matches_saved']}"
        )

        print(
            f"Existing matches reused: "
            f"{result['existing_matches_reused']}"
        )

        print(
            f"Cross-platform skipped: "
            f"{result['cross_platform_skipped']}"
        )

        print(
            f"Wrong queue skipped: "
            f"{result['wrong_queue_skipped']}"
        )

        print(
            f"Failed matches: "
            f"{result['failed_matches']}"
        )

        # ==========================================
        # DISTRIBUTIONS
        # ==========================================

        if (
            not df.empty
            and
            "role"
            in df.columns
        ):

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

        if (
            not df.empty
            and
            "division"
            in df.columns
        ):

            print()

            print(
                "DIVISION COUNTS"
            )

            print(
                df[
                    "division"
                ].value_counts(
                    dropna=False
                )
            )

        if (
            not df.empty
            and
            "match_platform"
            in df.columns
        ):

            print()

            print(
                "MATCH PLATFORM COUNTS"
            )

            print(
                df[
                    "match_platform"
                ].value_counts(
                    dropna=False
                )
            )

        print()

        print(
            f"Saved: "
            f"{OUTPUT_PATH}"
        )

    finally:

        riot_client.close()

        db.close()


if __name__ == "__main__":

    main()