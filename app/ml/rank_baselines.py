from dataclasses import dataclass


@dataclass
class RankedPlayerSample:

    puuid: str

    tier: str

    division: str | None

    league_points: int | None

    wins: int | None

    losses: int | None

    platform: str

    rank_bucket: str