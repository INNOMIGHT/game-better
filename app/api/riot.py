from fastapi import APIRouter, HTTPException

from app.riot.client import RiotClient


router = APIRouter(
    prefix="/riot",
    tags=["Riot"],
)


@router.get("/account")
def get_riot_account(
    game_name: str,
    tag_line: str,
):
    client = RiotClient()

    try:
        return client.get_account_by_riot_id(
            game_name,
            tag_line,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:
        client.close()