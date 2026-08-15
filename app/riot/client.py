import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class RiotClient:

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

    def get_account_by_puuid(
        self,
        puuid: str,
        region: str = "europe",
    ):
        url = (
            f"https://{region}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-puuid/{puuid}"
        )

        response = self.client.get(url)

        response.raise_for_status()

        return response.json()

    def close(self):
        self.client.close()