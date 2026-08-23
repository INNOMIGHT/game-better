import os
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


load_dotenv()


class RiotClient:
    ACCOUNT_REGION_URL = "https://europe.api.riotgames.com"

    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")

        if not self.api_key:
            raise ValueError(
                "RIOT_API_KEY environment variable is not configured."
            )

        self.client = httpx.Client(
            headers={
                "X-Riot-Token": self.api_key,
            },
            timeout=10.0,
        )

    def get_account_by_riot_id(
        self,
        game_name: str,
        tag_line: str,
    ) -> dict:

        encoded_game_name = quote(game_name, safe="")
        encoded_tag_line = quote(tag_line, safe="")

        url = (
            f"{self.ACCOUNT_REGION_URL}"
            f"/riot/account/v1/accounts/by-riot-id/"
            f"{encoded_game_name}/{encoded_tag_line}"
        )

        response = self.client.get(url)
        response.raise_for_status()

        return response.json()

    def get_summoner_by_puuid(
        self,
        puuid: str,
        platform: str,
    ) -> dict:

        platform = platform.lower()

        url = (
            f"https://{platform}.api.riotgames.com"
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        )

        response = self.client.get(url)
        response.raise_for_status()

        return response.json()

    def close(self):
        self.client.close()