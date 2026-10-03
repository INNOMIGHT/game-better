
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.match_service import MatchService


router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


@router.post("/sync")
def sync_ranked_matches(
    riot_account_id: int,
    platform: str,
    count: int = 10,
    db: Session = Depends(get_db),
):

    service = MatchService(db)

    try:
        return service.sync_ranked_matches(
            riot_account_id=riot_account_id,
            platform=platform,
            count=count,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to synchronize matches.",
        )