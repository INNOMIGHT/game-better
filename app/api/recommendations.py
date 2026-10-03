
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.recommendation import CoachingOverview
from app.services.recommendation_service import RecommendationService


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "/riot-account/{riot_account_id}",
    response_model=CoachingOverview,
)
def get_recommendations(
    riot_account_id: int,
    db: Session = Depends(get_db),
):
    service = RecommendationService(db)

    try:
        return service.get_coaching_overview(riot_account_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )