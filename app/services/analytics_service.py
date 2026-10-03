from statistics import mean

from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    MatchPerformance,
    PlayerOverview,
)


class AnalyticsService:

    def __init__(self, db):
        self.repository = AnalyticsRepository(db)

    @staticmethod
    def safe_divide(numerator, denominator):

        if denominator is None or denominator <= 0:
            return None

        return numerator / denominator

    @staticmethod
    def average(values):

        valid_values = [
            value
            for value in values
            if value is not None
        ]

        if not valid_values:
            return None

        return round(mean(valid_values), 2)

    def get_player_overview(
        self,
        riot_account_id: int,
    ):

        account_data = self.repository.get_riot_account(
            riot_account_id
        )

        if account_data is None:
            return None

        riot_account, league_profile = account_data

        records = self.repository.get_player_matches(
            puuid=riot_account.puuid,
            limit=10,
        )

        if not records:
            return {
                "riot_account_id": riot_account.id,
                "puuid": riot_account.puuid,
                "total_matches": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "average_kills": 0.0,
                "average_deaths": 0.0,
                "average_assists": 0.0,
                "average_kda": 0.0,
                "average_kill_participation": None,
                "average_gold_per_minute": None,
                "average_cs_per_minute": None,
                "average_vision_score": None,
                "matches": [],
            }

        match_performances = []

        for record in records:

            match = record["match"]
            player = record["player"]
            participants = record["participants"]

            duration_seconds = match.game_duration or 0
            duration_minutes = duration_seconds / 60

            team_kills = sum(
                participant.kills or 0
                for participant in participants
                if participant.team_id == player.team_id
            )

            kills = player.kills or 0
            deaths = player.deaths or 0
            assists = player.assists or 0

            kda = (
                kills + assists
            ) / max(deaths, 1)

            kill_participation = self.safe_divide(
                kills + assists,
                team_kills,
            )

            gold_earned = player.gold_earned

            gold_per_minute = self.safe_divide(
                gold_earned,
                duration_minutes,
            )

            cs = (
                (player.total_minions_killed or 0)
                + (player.neutral_minions_killed or 0)
            )

            cs_per_minute = self.safe_divide(
                cs,
                duration_minutes,
            )

            raw_data = player.raw_data or {}

            vision_score = raw_data.get("visionScore")

            performance = MatchPerformance(
                match_id=match.match_id,
                game_version=match.game_version,

                champion_name=player.champion_name,
                role=player.role,

                game_duration_minutes=round(
                    duration_minutes,
                    2,
                ),

                win=bool(player.win),

                kills=kills,
                deaths=deaths,
                assists=assists,

                kda=round(kda, 2),

                kill_participation=(
                    round(kill_participation * 100, 2)
                    if kill_participation is not None
                    else None
                ),

                gold_earned=gold_earned,

                gold_per_minute=(
                    round(gold_per_minute, 2)
                    if gold_per_minute is not None
                    else None
                ),

                cs=cs,

                cs_per_minute=(
                    round(cs_per_minute, 2)
                    if cs_per_minute is not None
                    else None
                ),

                vision_score=vision_score,
                wards_placed=player.wards_placed,
                wards_killed=player.wards_killed,
            )

            match_performances.append(performance)

        total_matches = len(match_performances)

        wins = sum(
            1 for match in match_performances
            if match.win
        )

        losses = total_matches - wins

        return PlayerOverview(
            riot_account_id=riot_account.id,
            puuid=riot_account.puuid,

            total_matches=total_matches,
            wins=wins,
            losses=losses,

            win_rate=round(
                wins / total_matches * 100,
                2,
            ),

            average_kills=self.average(
                [m.kills for m in match_performances]
            ),

            average_deaths=self.average(
                [m.deaths for m in match_performances]
            ),

            average_assists=self.average(
                [m.assists for m in match_performances]
            ),

            average_kda=self.average(
                [m.kda for m in match_performances]
            ),

            average_kill_participation=self.average(
                [
                    m.kill_participation
                    for m in match_performances
                ]
            ),

            average_gold_per_minute=self.average(
                [
                    m.gold_per_minute
                    for m in match_performances
                ]
            ),

            average_cs_per_minute=self.average(
                [
                    m.cs_per_minute
                    for m in match_performances
                ]
            ),

            average_vision_score=self.average(
                [
                    m.vision_score
                    for m in match_performances
                ]
            ),

            matches=match_performances,
        )