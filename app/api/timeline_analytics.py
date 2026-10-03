from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.timeline_analytics import (
    TimelinePlayerOverview,
)

from app.services.timeline_analytics_service import (
    TimelineAnalyticsService,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Timeline Analytics"],
)


@router.get(
    "/riot-account/{riot_account_id}/timeline",
    response_model=TimelinePlayerOverview,
)
def get_player_timeline(
    riot_account_id: int,
    db: Session = Depends(get_db),
):

    service = TimelineAnalyticsService(db)

    result = service.get_player_timeline_overview(
        riot_account_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Riot account or League profile not found",
        )

    return result