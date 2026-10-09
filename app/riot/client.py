import os
import time
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


load_dotenv()


class RiotClient:

    ACCOUNT_REGION_URL = (
        "https://europe.api.riotgames.com"
    )

    ROUTING_REGIONS = {
        "AMERICAS",
        "EUROPE",
        "ASIA",
        "SEA",
    }

    MAX_RETRIES = 5
    DEFAULT_RETRY_SECONDS = 2

    def __init__(self):

        self.api_key = os.getenv(
            "RIOT_API_KEY"
        )

        if not self.api_key:

            raise ValueError(
                "RIOT_API_KEY environment variable "
                "is not configured."
            )

        self.client = httpx.Client(
            headers={
                "X-Riot-Token":
                    self.api_key,
            },
            timeout=30.0,
        )

    # ==================================================
    # INTERNAL REQUEST HANDLER
    # ==================================================

    def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:

        last_exception = None

        for attempt in range(
            1,
            self.MAX_RETRIES + 1,
        ):

            try:

                response = (
                    self.client.request(
                        method,
                        url,
                        **kwargs,
                    )
                )

            except httpx.RequestError as exc:

                last_exception = exc

                if (
                    attempt
                    == self.MAX_RETRIES
                ):

                    raise

                wait_seconds = min(
                    self.DEFAULT_RETRY_SECONDS
                    * (
                        2
                        ** (
                            attempt - 1
                        )
                    ),
                    30,
                )

                print(
                    "Riot request network error. "
                    f"Retrying in {wait_seconds}s "
                    f"(attempt "
                    f"{attempt}/"
                    f"{self.MAX_RETRIES})"
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # ==========================================
            # RATE LIMIT
            # ==========================================

            if (
                response.status_code
                == 429
            ):

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                try:

                    wait_seconds = int(
                        retry_after
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    wait_seconds = (
                        self.DEFAULT_RETRY_SECONDS
                        * (
                            2
                            ** (
                                attempt - 1
                            )
                        )
                    )

                wait_seconds = max(
                    wait_seconds,
                    1,
                )

                rate_limit_type = (
                    response.headers.get(
                        "X-Rate-Limit-Type"
                    )
                )

                print(
                    "Riot API rate limit hit"
                    f"{' [' + rate_limit_type + ']' if rate_limit_type else ''}. "
                    f"Waiting {wait_seconds}s "
                    f"(attempt "
                    f"{attempt}/"
                    f"{self.MAX_RETRIES})"
                )

                if (
                    attempt
                    == self.MAX_RETRIES
                ):

                    response.raise_for_status()

                time.sleep(
                    wait_seconds
                )

                continue

            # ==========================================
            # TEMPORARY SERVER ERRORS
            # ==========================================

            if (
                response.status_code
                in {
                    500,
                    502,
                    503,
                    504,
                }
            ):

                if (
                    attempt
                    == self.MAX_RETRIES
                ):

                    response.raise_for_status()

                wait_seconds = min(
                    self.DEFAULT_RETRY_SECONDS
                    * (
                        2
                        ** (
                            attempt - 1
                        )
                    ),
                    30,
                )

                print(
                    "Riot API temporary error "
                    f"{response.status_code}. "
                    f"Retrying in {wait_seconds}s "
                    f"(attempt "
                    f"{attempt}/"
                    f"{self.MAX_RETRIES})"
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # ==========================================
            # NORMAL RESPONSE
            # ==========================================

            response.raise_for_status()

            return response

        if last_exception:

            raise last_exception

        raise RuntimeError(
            "Riot request failed unexpectedly."
        )

    # ==================================================
    # ACCOUNT-V1
    # ==================================================

    def get_account_by_riot_id(
        self,
        game_name: str,
        tag_line: str,
    ) -> dict:

        encoded_game_name = quote(
            game_name,
            safe="",
        )

        encoded_tag_line = quote(
            tag_line,
            safe="",
        )

        url = (
            f"{self.ACCOUNT_REGION_URL}"
            "/riot/account/v1/"
            "accounts/by-riot-id/"
            f"{encoded_game_name}/"
            f"{encoded_tag_line}"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    # ==================================================
    # SUMMONER-V4
    # ==================================================

    def get_summoner_by_puuid(
        self,
        puuid: str,
        platform: str,
    ) -> dict:

        platform = (
            platform.lower()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/summoner/v4/"
            f"summoners/by-puuid/{puuid}"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    def get_summoner_by_id(
        self,
        summoner_id: str,
        platform: str,
    ) -> dict:

        platform = (
            platform.lower()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/summoner/v4/"
            f"summoners/{summoner_id}"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    # ==================================================
    # MATCH-V5
    # ==================================================

    def get_ranked_match_ids(
        self,
        puuid: str,
        region: str,
        start: int = 0,
        count: int = 20,
        queue: int = 420,
    ) -> list[str]:

        region = (
            region.upper()
        )

        if (
            region
            not in self.ROUTING_REGIONS
        ):

            raise ValueError(
                "Unsupported Riot routing region: "
                f"{region}"
            )

        url = (
            f"https://{region.lower()}.api.riotgames.com"
            "/lol/match/v5/"
            f"matches/by-puuid/{puuid}/ids"
        )

        response = (
            self._request(
                "GET",
                url,
                params={
                    "start":
                        start,

                    "count":
                        count,

                    "queue":
                        queue,
                },
            )
        )

        return response.json()

    def get_match_by_id(
        self,
        match_id: str,
        region: str,
    ) -> dict:

        region = (
            region.upper()
        )

        if (
            region
            not in self.ROUTING_REGIONS
        ):

            raise ValueError(
                "Unsupported Riot routing region: "
                f"{region}"
            )

        url = (
            f"https://{region.lower()}.api.riotgames.com"
            "/lol/match/v5/"
            f"matches/{match_id}"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    def get_match_timeline(
        self,
        match_id: str,
        region: str,
    ) -> dict:

        region = (
            region.upper()
        )

        if (
            region
            not in self.ROUTING_REGIONS
        ):

            raise ValueError(
                "Unsupported Riot routing region: "
                f"{region}"
            )

        url = (
            f"https://{region.lower()}.api.riotgames.com"
            "/lol/match/v5/"
            f"matches/{match_id}/timeline"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    # ==================================================
    # LEAGUE-V4
    #
    # GOLD / PLATINUM / EMERALD / DIAMOND
    # ==================================================

    def get_ranked_entries(
        self,
        platform: str,
        tier: str,
        division: str,
        page: int = 1,
    ) -> list[dict]:

        platform = (
            platform.lower()
        )

        tier = (
            tier.upper()
        )

        division = (
            division.upper()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/league/v4/"
            "entries/"
            "RANKED_SOLO_5x5/"
            f"{tier}/"
            f"{division}"
        )

        response = (
            self._request(
                "GET",
                url,
                params={
                    "page":
                        page,
                },
            )
        )

        return response.json()

    # ==================================================
    # LEAGUE-V4
    #
    # MASTER+
    # ==================================================

    def get_master_league(
        self,
        platform: str,
    ) -> dict:

        platform = (
            platform.lower()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/league/v4/"
            "masterleagues/by-queue/"
            "RANKED_SOLO_5x5"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    def get_grandmaster_league(
        self,
        platform: str,
    ) -> dict:

        platform = (
            platform.lower()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/league/v4/"
            "grandmasterleagues/by-queue/"
            "RANKED_SOLO_5x5"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    def get_challenger_league(
        self,
        platform: str,
    ) -> dict:

        platform = (
            platform.lower()
        )

        url = (
            f"https://{platform}.api.riotgames.com"
            "/lol/league/v4/"
            "challengerleagues/by-queue/"
            "RANKED_SOLO_5x5"
        )

        response = (
            self._request(
                "GET",
                url,
            )
        )

        return response.json()

    # ==================================================
    # CLEANUP
    # ==================================================

    def close(
        self,
    ):

        self.client.close()

    def __enter__(
        self,
    ):

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.close()