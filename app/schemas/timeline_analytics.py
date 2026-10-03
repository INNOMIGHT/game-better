from pydantic import BaseModel


class PhasePerformance(BaseModel):
    phase: str

    start_minute: float
    end_minute: float

    cs_gained: int | None
    cs_per_minute: float | None

    deaths: int


class MatchTimelinePerformance(BaseModel):
    match_id: str
    game_version: str | None

    champion_name: str | None
    role: str | None

    game_duration_minutes: float

    early_game: PhasePerformance
    mid_game: PhasePerformance
    late_game: PhasePerformance

    cs_rate_change_mid_vs_early: float | None
    cs_rate_change_late_vs_mid: float | None


class TimelinePlayerOverview(BaseModel):
    riot_account_id: int
    puuid: str

    total_matches: int

    average_early_cs_per_minute: float | None
    average_mid_cs_per_minute: float | None
    average_late_cs_per_minute: float | None

    average_early_deaths: float
    average_mid_deaths: float
    average_late_deaths: float

    matches: list[MatchTimelinePerformance]