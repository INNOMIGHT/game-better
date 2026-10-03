from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.riot_account import RiotAccount
from app.models.league_profile import LeagueProfile
from app.models.match import Match
from app.models.match_participant import MatchParticipant

from app.models.timeline_frame import TimelineFrame
from app.models.timeline_event import TimelineEvent


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

    def get_timeline_frames(self, match_ids: list[int]):

        if not match_ids:
            return []

        statement = (
            select(TimelineFrame)
            .where(TimelineFrame.match_id.in_(match_ids))
            .order_by(
                TimelineFrame.match_id,
                TimelineFrame.participant_id,
                TimelineFrame.timestamp_ms,
            )
        )

        return (
            self.db.execute(statement)
            .scalars()
            .all()
        )


    def get_timeline_events(self, match_ids: list[int]):

        if not match_ids:
            return []

        statement = (
            select(TimelineEvent)
            .where(TimelineEvent.match_id.in_(match_ids))
            .order_by(
                TimelineEvent.match_id,
                TimelineEvent.timestamp_ms,
            )
        )

        return (
            self.db.execute(statement)
            .scalars()
            .all()
        )