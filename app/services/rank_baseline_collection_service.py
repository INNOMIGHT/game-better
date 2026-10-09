from datetime import datetime, timezone

from app.models.match import Match


class RankBaselineCollectionService:

    QUEUE_ID = 420

    def __init__(
        self,
        db,
        riot_client,
        match_repository,
    ):
        self.db = db
        self.riot_client = riot_client
        self.match_repository = match_repository

    # ==================================================
    # DATABASE
    # ==================================================

    def _get_existing_match(
        self,
        match_id,
    ):

        return (
            self.db
            .query(Match)
            .filter(
                Match.match_id
                == match_id
            )
            .first()
        )

    # ==================================================
    # RAW DATA
    # ==================================================

    @staticmethod
    def _get_stored_match_data(
        match,
    ):
        """
        MatchRepository stores raw_data roughly as:

        {
            "match": {...},
            "timeline": {...}
        }

        Return stored Match-v5 response when available.
        """

        raw_data = (
            getattr(
                match,
                "raw_data",
                None,
            )
            or {}
        )

        if not isinstance(
            raw_data,
            dict,
        ):
            return None

        match_data = (
            raw_data.get(
                "match"
            )
        )

        if not isinstance(
            match_data,
            dict,
        ):
            return None

        return match_data

    # ==================================================
    # PARTICIPANT
    # ==================================================

    @staticmethod
    def _find_participant(
        match_data,
        puuid,
    ):

        participants = (
            match_data
            .get(
                "info",
                {}
            )
            .get(
                "participants",
                [],
            )
        )

        for participant in participants:

            if (
                participant.get(
                    "puuid"
                )
                == puuid
            ):
                return participant

        return None

    # ==================================================
    # MAIN COLLECTION
    # ==================================================

    def collect_for_players(
        self,
        *,
        players,
        region,
        expected_platform,
        matches_per_player=5,
        target_unique_matches=200,
    ):

        expected_platform = (
            expected_platform.upper()
        )

        rows = []

        unique_match_ids = set()

        failed_matches = 0

        existing_matches_reused = 0

        new_matches_saved = 0

        cross_platform_skipped = 0

        wrong_queue_skipped = 0

        # ==================================================
        # PLAYERS
        # ==================================================

        for player_index, player in enumerate(
            players,
            start=1,
        ):

            if (
                len(unique_match_ids)
                >= target_unique_matches
            ):
                break

            print(
                f"Player "
                f"{player_index}/"
                f"{len(players)} "
                f"{player.tier} "
                f"{player.division or ''} "
                f"- collected "
                f"{len(unique_match_ids)}/"
                f"{target_unique_matches} matches"
            )

            # ----------------------------------------------
            # Recent ranked match IDs
            # ----------------------------------------------

            try:

                match_ids = (
                    self.riot_client
                    .get_ranked_match_ids(
                        puuid=
                            player.puuid,

                        region=
                            region,

                        start=
                            0,

                        count=
                            matches_per_player,

                        queue=
                            self.QUEUE_ID,
                    )
                )

            except Exception as exc:

                print(
                    f"Failed player "
                    f"{player.puuid}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                continue

            # ==================================================
            # MATCHES
            # ==================================================

            for match_id in match_ids:

                if (
                    len(unique_match_ids)
                    >= target_unique_matches
                ):
                    break

                # ----------------------------------------------
                # Don't label same match twice within THIS
                # rank collection.
                # ----------------------------------------------

                if (
                    match_id
                    in unique_match_ids
                ):
                    continue

                try:

                    existing_match = (
                        self._get_existing_match(
                            match_id
                        )
                    )

                    match_data = None

                    match_was_existing = (
                        existing_match
                        is not None
                    )

                    # ==========================================
                    # REUSE EXISTING DATABASE MATCH
                    # ==========================================

                    if match_was_existing:

                        match_data = (
                            self._get_stored_match_data(
                                existing_match
                            )
                        )

                        # Stored raw match data unavailable.
                        # Fetch match again, but DON'T insert it.
                        if match_data is None:

                            match_data = (
                                self.riot_client
                                .get_match_by_id(
                                    match_id=
                                        match_id,

                                    region=
                                        region,
                                )
                            )

                    # ==========================================
                    # NEW MATCH
                    # ==========================================

                    else:

                        match_data = (
                            self.riot_client
                            .get_match_by_id(
                                match_id=
                                    match_id,

                                region=
                                    region,
                            )
                        )

                    info = (
                        match_data
                        .get(
                            "info",
                            {}
                        )
                    )

                    # ==========================================
                    # QUEUE VALIDATION
                    # ==========================================

                    queue_id = (
                        info.get(
                            "queueId"
                        )
                    )

                    if (
                        queue_id
                        != self.QUEUE_ID
                    ):

                        wrong_queue_skipped += 1

                        print(
                            f"Skipping "
                            f"{match_id}: "
                            f"queueId="
                            f"{queue_id}"
                        )

                        continue

                    # ==========================================
                    # PLATFORM VALIDATION
                    #
                    # Important for players who may have
                    # transferred regions. Match-v5 history
                    # can contain old matches from another
                    # platform.
                    # ==========================================

                    match_platform = (
                        info.get(
                            "platformId"
                        )
                        or ""
                    ).upper()

                    if (
                        match_platform
                        != expected_platform
                    ):

                        cross_platform_skipped += 1

                        print(
                            f"Skipping "
                            f"{match_id}: "
                            f"platform="
                            f"{match_platform}, "
                            f"expected="
                            f"{expected_platform}"
                        )

                        continue

                    # ==========================================
                    # FIND THE RANK-LABELLED PLAYER
                    # ==========================================

                    participant = (
                        self._find_participant(
                            match_data=
                                match_data,

                            puuid=
                                player.puuid,
                        )
                    )

                    if participant is None:

                        print(
                            f"Skipping "
                            f"{match_id}: "
                            "sampled player "
                            "not found."
                        )

                        continue

                    # ==========================================
                    # SAVE ONLY IF NEW
                    # ==========================================

                    if match_was_existing:

                        existing_matches_reused += 1

                        print(
                            f"  Reused "
                            f"{match_id}"
                        )

                    else:

                        timeline_data = (
                            self.riot_client
                            .get_match_timeline(
                                match_id=
                                    match_id,

                                region=
                                    region,
                            )
                        )

                        self.match_repository.save_match(
                            match_data=
                                match_data,

                            timeline_data=
                                timeline_data,
                        )

                        self.db.commit()

                        new_matches_saved += 1

                        print(
                            f"  Saved "
                            f"{match_id}"
                        )

                    # ==========================================
                    # MATCH NOW COUNTS AS A VALID BASELINE ROW
                    # ==========================================

                    unique_match_ids.add(
                        match_id
                    )

                    rows.append({
                        "match_id":
                            match_id,

                        "puuid":
                            player.puuid,

                        "platform":
                            player.platform,

                        "match_platform":
                            match_platform,

                        "rank_bucket":
                            player.rank_bucket,

                        "tier":
                            player.tier,

                        "division":
                            player.division,

                        "league_points":
                            player.league_points,

                        "collection_time":
                            datetime.now(
                                timezone.utc
                            ).isoformat(),

                        "game_version":
                            info.get(
                                "gameVersion"
                            ),

                        "participant_id":
                            participant.get(
                                "participantId"
                            ),

                        "role":
                            (
                                participant.get(
                                    "teamPosition"
                                )
                                or
                                participant.get(
                                    "individualPosition"
                                )
                            ),

                        "champion":
                            participant.get(
                                "championName"
                            ),

                        "win":
                            participant.get(
                                "win"
                            ),
                    })

                    print(
                        f"    "
                        f"{len(unique_match_ids)}/"
                        f"{target_unique_matches}"
                    )

                except Exception as exc:

                    self.db.rollback()

                    failed_matches += 1

                    print(
                        f"Failed match "
                        f"{match_id}: "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                    continue

        # ==================================================
        # RESULT
        # ==================================================

        return {
            "rows":
                rows,

            "unique_matches":
                len(
                    unique_match_ids
                ),

            "new_matches_saved":
                new_matches_saved,

            "existing_matches_reused":
                existing_matches_reused,

            "cross_platform_skipped":
                cross_platform_skipped,

            "wrong_queue_skipped":
                wrong_queue_skipped,

            "failed_matches":
                failed_matches,
        }