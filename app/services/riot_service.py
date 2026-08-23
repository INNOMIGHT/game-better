from sqlalchemy.orm import Session

from app.repositories.riot_account_repository import RiotAccountRepository
from app.repositories.user_repository import UserRepository
from app.riot.client import RiotClient
from app.repositories.league_profile_repository import LeagueProfileRepository

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
        self.league_profile_repository = LeagueProfileRepository(db)


    # VS added Region mapping for League Servers 
    def get_region_from_platform(self, platform: str) -> str:
        regions = {
            "EUW1": "EUROPE",
            "EUN1": "EUROPE",
            "TR1": "EUROPE",
            "RU": "EUROPE",
            "NA1": "AMERICAS",
            "BR1": "AMERICAS",
            "LA1": "AMERICAS",
            "LA2": "AMERICAS",
            "OC1": "SEA",
            "JP1": "ASIA",
            "KR": "ASIA",
            "PH2": "SEA",
            "SG2": "SEA",
            "TH2": "SEA",
            "TW2": "SEA",
            "VN2": "SEA",
            "ME1": "EUROPE",
        }

        normalized_platform = platform.upper()

        if normalized_platform not in regions:
            raise ValueError(
                f"Unsupported League platform: {platform}"
            )

        return regions[normalized_platform]


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


    def sync_league_profile(self, riot_account_id: int, platform: str):

        riot_account = (
            self.riot_account_repository
            .get_by_id(riot_account_id)
        )

        if not riot_account:
            raise ValueError("Riot account not found.")

        league_data = self.riot_client.get_summoner_by_puuid(
            puuid=riot_account.puuid,
            platform=platform,
        )

        region = self.get_region_from_platform(platform)

        existing_profile = (
            self.league_profile_repository
            .get_by_riot_account_id(riot_account_id)
        )

        if existing_profile:
            profile = self.league_profile_repository.update(
                profile=existing_profile,
                summoner_level=league_data.get("summonerLevel"),
                profile_icon_id=league_data.get("profileIconId"),
            )
        else:
            profile = self.league_profile_repository.create(
                riot_account_id=riot_account_id,
                platform=platform,
                region=region,
                summoner_level=league_data.get("summonerLevel"),
                profile_icon_id=league_data.get("profileIconId"),
            )

        self.db.commit()

        return profile