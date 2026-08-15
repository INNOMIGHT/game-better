from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.riot_account import RiotAccountResponse
from app.services.riot_service import RiotService


router = APIRouter(
    prefix="/riot",
    tags=["Riot"],
)


@router.post(
    "/sync",
    response_model=RiotAccountResponse,
)
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