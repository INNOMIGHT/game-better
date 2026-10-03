from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.riot_account import RiotAccount
from app.models.league_profile import LeagueProfile
from app.models.match import Match
from app.models.match_participant import MatchParticipant


class AnalyticsRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_riot_account(self, riot_account_id: int):

        statement = (
            select(RiotAccount, LeagueProfile)
            .join(
                LeagueProfile,
                LeagueProfile.riot_account_id == RiotAccount.id,
            )
            .where(RiotAccount.id == riot_account_id)
        )

        return self.db.execute(statement).first()

    def get_player_matches(
        self,
        puuid: str,
        limit: int = 10,
    ):

        statement = (
            select(Match, MatchParticipant)
            .join(
                MatchParticipant,
                MatchParticipant.match_id == Match.id,
            )
            .where(
                MatchParticipant.puuid == puuid,
                Match.queue_id == 420,
            )
            .order_by(Match.game_creation.desc())
            .limit(limit)
        )

        results = self.db.execute(statement).all()

        if not results:
            return []

        match_ids = [
            match.id
            for match, player in results
        ]

        participants_statement = (
            select(MatchParticipant)
            .where(
                MatchParticipant.match_id.in_(match_ids)
            )
        )

        all_participants = (
            self.db.execute(participants_statement)
            .scalars()
            .all()
        )

        participants_by_match = {}

        for participant in all_participants:

            participants_by_match.setdefault(
                participant.match_id,
                [],
            ).append(participant)

        return [
            {
                "match": match,
                "player": player,
                "participants": participants_by_match.get(
                    match.id,
                    [],
                ),
            }
            for match, player in results
        ]