from collections import deque

from sqlalchemy.orm import Session

from app.models.riot_account import RiotAccount
from app.models.league_profile import LeagueProfile
from app.models.match_participant import MatchParticipant

from app.repositories.match_repository import MatchRepository
from app.riot.client import RiotClient


class MLMatchCollectionService:

    def __init__(self, db: Session):
        self.db = db
        self.match_repository = MatchRepository(db)

    def collect_from_account(
        self,
        riot_account_id: int,
        platform: str,
        target_new_matches: int = 300,
        matches_per_player: int = 20,
        max_players: int = 100,
    ) -> dict:

        platform = platform.upper()

        if target_new_matches < 1:
            raise ValueError(
                "target_new_matches must be greater than 0."
            )

        if matches_per_player < 1 or matches_per_player > 20:
            raise ValueError(
                "matches_per_player must be between 1 and 20."
            )

        if max_players < 1:
            raise ValueError(
                "max_players must be greater than 0."
            )

        account = (
            self.db.query(RiotAccount)
            .filter(RiotAccount.id == riot_account_id)
            .first()
        )

        if not account:
            raise ValueError("Riot account not found.")

        profile = (
            self.db.query(LeagueProfile)
            .filter(
                LeagueProfile.riot_account_id
                == riot_account_id
            )
            .first()
        )

        if not profile:
            raise ValueError(
                "League profile not found."
            )

        if profile.platform.upper() != platform:
            raise ValueError(
                "Selected platform does not match "
                "the saved League profile."
            )

        region = profile.region.upper()

        player_queue = deque([account.puuid])

        queued_puuids = {account.puuid}
        visited_puuids = set()

        seen_match_ids = set()

        result = {
            "seed_riot_account_id": riot_account_id,
            "platform": platform,
            "region": region,
            "target_new_matches": target_new_matches,
            "matches_per_player": matches_per_player,
            "max_players": max_players,

            "players_processed": 0,
            "players_discovered": 1,

            "match_ids_discovered": 0,

            "new_matches_saved": 0,
            "existing_matches_seen": 0,

            "failed_match_count": 0,
            "failed_player_count": 0,

            "failed_matches": [],
            "failed_players": [],
        }

        with RiotClient() as riot:

            while player_queue:

                if (
                    result["new_matches_saved"]
                    >= target_new_matches
                ):
                    break

                if (
                    result["players_processed"]
                    >= max_players
                ):
                    break

                puuid = player_queue.popleft()

                if puuid in visited_puuids:
                    continue

                visited_puuids.add(puuid)

                result["players_processed"] += 1

                print()
                print(
                    f"Processing player "
                    f"{result['players_processed']}/"
                    f"{max_players}"
                )

                print(
                    f"Saved matches: "
                    f"{result['new_matches_saved']}/"
                    f"{target_new_matches}"
                )

                try:
                    match_ids = riot.get_ranked_match_ids(
                        puuid=puuid,
                        region=region,
                        start=0,
                        count=matches_per_player,
                        queue=420,
                    )

                except Exception as exc:

                    result["failed_player_count"] += 1

                    result["failed_players"].append({
                        "puuid": puuid,
                        "error": str(exc),
                    })

                    print(
                        f"Failed to fetch matches "
                        f"for player: {exc}"
                    )

                    continue

                for match_id in match_ids:

                    if (
                        result["new_matches_saved"]
                        >= target_new_matches
                    ):
                        break

                    if match_id in seen_match_ids:
                        continue

                    seen_match_ids.add(match_id)

                    result["match_ids_discovered"] += 1

                    existing_match = (
                        self.match_repository
                        .get_by_match_id(match_id)
                    )

                    # ----------------------------------
                    # MATCH ALREADY EXISTS
                    # ----------------------------------

                    if existing_match:

                        result[
                            "existing_matches_seen"
                        ] += 1

                        existing_participants = (
                            self.db.query(
                                MatchParticipant
                            )
                            .filter(
                                MatchParticipant.match_id
                                == existing_match.id
                            )
                            .all()
                        )

                        self._queue_participants(
                            participants=[
                                participant.puuid
                                for participant
                                in existing_participants
                            ],
                            player_queue=player_queue,
                            queued_puuids=queued_puuids,
                        )

                        continue

                    # ----------------------------------
                    # NEW MATCH
                    # ----------------------------------

                    try:
                        match_data = riot.get_match_by_id(
                            match_id=match_id,
                            region=region,
                        )

                        if (
                            match_data["info"]
                            .get("queueId")
                            != 420
                        ):
                            continue

                        timeline_data = (
                            riot.get_match_timeline(
                                match_id=match_id,
                                region=region,
                            )
                        )

                        saved_match = (
                            self.match_repository
                            .save_match(
                                match_data=match_data,
                                timeline_data=timeline_data,
                            )
                        )

                        self.db.commit()

                        result[
                            "new_matches_saved"
                        ] += 1

                        print(
                            f"Saved "
                            f"{match_id} "
                            f"("
                            f"{result['new_matches_saved']}"
                            f"/"
                            f"{target_new_matches}"
                            f")"
                        )

                        participant_puuids = [
                            participant["puuid"]
                            for participant
                            in match_data["info"][
                                "participants"
                            ]
                            if participant.get("puuid")
                        ]

                        self._queue_participants(
                            participants=participant_puuids,
                            player_queue=player_queue,
                            queued_puuids=queued_puuids,
                        )

                    except Exception as exc:

                        self.db.rollback()

                        result[
                            "failed_match_count"
                        ] += 1

                        result[
                            "failed_matches"
                        ].append({
                            "match_id": match_id,
                            "error": str(exc),
                        })

                        print(
                            f"Failed match "
                            f"{match_id}: {exc}"
                        )

        result["players_discovered"] = len(
            queued_puuids
        )

        result["players_remaining_in_queue"] = len(
            player_queue
        )

        result["unique_match_ids_seen"] = len(
            seen_match_ids
        )

        return result

    @staticmethod
    def _queue_participants(
        participants,
        player_queue,
        queued_puuids,
    ):

        for participant_puuid in participants:

            if not participant_puuid:
                continue

            if participant_puuid in queued_puuids:
                continue

            queued_puuids.add(
                participant_puuid
            )

            player_queue.append(
                participant_puuid
            )