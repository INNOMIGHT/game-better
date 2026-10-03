
from sqlalchemy.orm import Session

from app.models.riot_account import RiotAccount
from app.models.league_profile import LeagueProfile

from app.repositories.match_repository import MatchRepository
from app.services.riot_service import RiotService
from app.riot.client import RiotClient


class MatchService:

    def __init__(self, db: Session):
        self.db = db
        self.match_repository = MatchRepository(db)

    def sync_ranked_matches(
        self,
        riot_account_id: int,
        platform: str,
        count: int = 10,
    ) -> dict:

        platform = platform.upper()

        if count < 1 or count > 20:
            raise ValueError(
                "Count must be between 1 and 20."
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
                LeagueProfile.riot_account_id == riot_account_id
            )
            .first()
        )

        if not profile:
            raise ValueError(
                "League profile not found. Sync the League profile first."
            )

        if profile.platform.upper() != platform:
            raise ValueError(
                "Selected platform does not match the saved League profile."
            )

        riot_service = RiotService(self.db)

        region = riot_service.get_region_from_platform(platform)

        result = {
            "riot_account_id": riot_account_id,
            "platform": platform,
            "region": region,
            "requested_matches": count,
            "fetched_matches": 0,
            "saved_matches": 0,
            "skipped_matches": 0,
            "failed_matches": [],
            "matches": [],
        }

        with RiotClient() as riot:

            match_ids = riot.get_ranked_match_ids(
                puuid=account.puuid,
                region=region,
                start=0,
                count=count,
                queue=420,
            )

            result["fetched_matches"] = len(match_ids)

            for match_id in match_ids:

                existing = (
                    self.match_repository.get_by_match_id(match_id)
                )

                if existing:
                    result["skipped_matches"] += 1

                    result["matches"].append({
                        "match_id": match_id,
                        "status": "already_exists",
                        "database_id": existing.id,
                    })

                    continue

                try:
                    match_data = riot.get_match_by_id(
                        match_id=match_id,
                        region=region,
                    )

                    timeline_data = riot.get_match_timeline(
                        match_id=match_id,
                        region=region,
                    )

                    if match_data["info"].get("queueId") != 420:
                        raise ValueError(
                            "Match is not Ranked Solo/Duo."
                        )

                    saved_match = self.match_repository.save_match(
                        match_data=match_data,
                        timeline_data=timeline_data,
                    )

                    self.db.commit()

                    result["saved_matches"] += 1

                    result["matches"].append({
                        "match_id": match_id,
                        "status": "saved",
                        "database_id": saved_match.id,
                    })

                except Exception as exc:

                    self.db.rollback()

                    result["failed_matches"].append({
                        "match_id": match_id,
                        "error": str(exc),
                    })

        return result