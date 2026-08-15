from sqlalchemy.orm import Session

from app.repositories.riot_account_repository import RiotAccountRepository
from app.repositories.user_repository import UserRepository
from app.riot.client import RiotClient


# Riot ID
#    ↓
# Ask Riot
#    ↓
# Get PUUID
#    ↓
# Does PUUID exist?
#    │
#    ├── YES → return existing RiotAccount
#    │
#    └── NO
#         ↓
#      Create User
#         ↓
#      Create RiotAccount
#         ↓
#      Commit transaction

# VS Explains current flow above

class RiotService:

    def __init__(self, db: Session):
        self.db = db

        self.riot_client = RiotClient()
        self.riot_account_repository = RiotAccountRepository(db)
        self.user_repository = UserRepository(db)

    def sync_riot_account(
        self,
        game_name: str,
        tag_line: str,
    ):
        riot_data = self.riot_client.get_account_by_riot_id(
            game_name,
            tag_line,
        )

        puuid = riot_data["puuid"]

        existing_account = (
            self.riot_account_repository.get_by_puuid(puuid)
        )

        if existing_account:
            return existing_account

        try:
            user = self.user_repository.create()

            riot_account = self.riot_account_repository.create(
                user_id=user.id,
                puuid=puuid,
                game_name=riot_data["gameName"],
                tag_line=riot_data["tagLine"],
            )

            self.db.commit()

            return riot_account

        except Exception:
            self.db.rollback()
            raise

        finally:
            self.riot_client.close()