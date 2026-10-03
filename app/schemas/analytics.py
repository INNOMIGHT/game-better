from pydantic import BaseModel


class MatchPerformance(BaseModel):
    match_id: str
    game_version: str | None

    champion_name: str | None
    role: str | None

    game_duration_minutes: float
    win: bool

    kills: int
    deaths: int
    assists: int
    kda: float

    kill_participation: float | None

    gold_earned: int | None
    gold_per_minute: float | None

    cs: int
    cs_per_minute: float | None

    vision_score: int | None
    wards_placed: int | None
    wards_killed: int | None


class PlayerOverview(BaseModel):
    riot_account_id: int
    puuid: str

    total_matches: int
    wins: int
    losses: int
    win_rate: float

    average_kills: float
    average_deaths: float
    average_assists: float
    average_kda: float

    average_kill_participation: float | None
    average_gold_per_minute: float | None
    average_cs_per_minute: float | None
    average_vision_score: float | None

    matches: list[MatchPerformance]