from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import PlayerOverview


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/riot-account/{riot_account_id}/overview",
    response_model=PlayerOverview,
)
def get_player_overview(
    riot_account_id: int,
    db: Session = Depends(get_db),
):

    service = AnalyticsService(db)

    overview = service.get_player_overview(
        riot_account_id
    )

    if overview is None:
        raise HTTPException(
            status_code=404,
            detail="Riot account or linked League profile not found",
        )

    return overview