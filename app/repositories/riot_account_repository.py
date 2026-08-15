from sqlalchemy.orm import Session

from app.models.riot_account import RiotAccount


class RiotAccountRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_puuid(self, puuid: str) -> RiotAccount | None:
        return (
            self.db.query(RiotAccount)
            .filter(RiotAccount.puuid == puuid)
            .first()
        )

    def create(
        self,
        user_id: int,
        puuid: str,
        game_name: str,
        tag_line: str,
    ) -> RiotAccount:

        riot_account = RiotAccount(
            user_id=user_id,
            puuid=puuid,
            game_name=game_name,
            tag_line=tag_line,
        )

        self.db.add(riot_account)
        self.db.flush()

        return riot_account