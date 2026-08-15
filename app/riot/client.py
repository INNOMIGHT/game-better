import os
import httpx
from dotenv import load_dotenv
from urllib.parse import quote


load_dotenv()


class RiotClient:
    BASE_URL = "https://europe.api.riotgames.com"

    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")

        print("RIOT KEY LOADED:", bool(self.api_key))
        print("RIOT KEY PREFIX:", self.api_key[:8] if self.api_key else None)

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
            f"{self.BASE_URL}"
            f"/riot/account/v1/accounts/by-riot-id/"
            f"{encoded_game_name}/{encoded_tag_line}"
        )

        response = self.client.get(url)

        if response.status_code != 200:
            print("RIOT STATUS:", response.status_code)
            print("RIOT RESPONSE:", response.text)

        response.raise_for_status()


        return response.json()
    

    def close(self):
        self.client.close()