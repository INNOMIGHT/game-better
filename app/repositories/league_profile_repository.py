from sqlalchemy.orm import Session

from app.models.league_profile import LeagueProfile
from datetime import datetime


class LeagueProfileRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_riot_account_id(
        self,
        riot_account_id: int,
    ) -> LeagueProfile | None:
        return (
            self.db.query(LeagueProfile)
            .filter(
                LeagueProfile.riot_account_id == riot_account_id
            )
            .first()
        )

    def create(
        self,
        riot_account_id: int,
        platform: str,
        region: str,
        summoner_level: int | None,
        profile_icon_id: int | None,
    ) -> LeagueProfile:

        profile = LeagueProfile(
            riot_account_id=riot_account_id,
            platform=platform.upper(),
            region=region.upper(),
            summoner_level=summoner_level,
            profile_icon_id=profile_icon_id,
            last_synced_at=datetime.utcnow(),
        )

        self.db.add(profile)
        self.db.flush()

        return profile

    def update(
        self,
        profile: LeagueProfile,
        summoner_level: int | None,
        profile_icon_id: int | None,
    ) -> LeagueProfile:

        profile.summoner_level = summoner_level
        profile.profile_icon_id = profile_icon_id
        profile.last_synced_at = datetime.utcnow()

        self.db.flush()

        return profile