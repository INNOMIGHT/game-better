from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.riot_service import RiotService
from app.schemas.league_profile import LeagueProfileResponse


router = APIRouter(
    prefix="/riot",
    tags=["Riot"],
)


@router.post("/sync")
def sync_riot_account(
    game_name: str,
    tag_line: str,
    db: Session = Depends(get_db),
):
    service = RiotService(db)

    return service.sync_riot_account(
        game_name=game_name,
        tag_line=tag_line,
    )


@router.get("/league-profile")
def get_league_profile(
    puuid: str,
    platform: str,
):
    from app.riot.client import RiotClient

    client = RiotClient()

    try:
        return client.get_summoner_by_puuid(
            puuid=puuid,
            platform=platform,
        )

    finally:
        client.close()


@router.post(
    "/league-profile/sync",
    response_model=LeagueProfileResponse,
)
def sync_league_profile(
    riot_account_id: int,
    platform: str,
    db: Session = Depends(get_db),
):
    service = RiotService(db)

    return service.sync_league_profile(
        riot_account_id=riot_account_id,
        platform=platform,
    )