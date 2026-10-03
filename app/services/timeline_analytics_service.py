from statistics import mean

from app.repositories.analytics_repository import AnalyticsRepository

from app.schemas.timeline_analytics import (
    PhasePerformance,
    MatchTimelinePerformance,
    TimelinePlayerOverview,
)


class TimelineAnalyticsService:

    EARLY_END = 14
    MID_END = 25

    def __init__(self, db):
        self.repository = AnalyticsRepository(db)

    @staticmethod
    def safe_divide(numerator, denominator):

        if denominator is None or denominator <= 0:
            return None

        return numerator / denominator

    @staticmethod
    def average(values):

        valid = [
            value
            for value in values
            if value is not None
        ]

        if not valid:
            return None

        return round(mean(valid), 2)

    @staticmethod
    def get_frame_cs(frame):

        if frame is None:
            return None

        lane_cs = frame.minions_killed or 0
        jungle_cs = frame.jungle_minions_killed or 0

        return lane_cs + jungle_cs

    @staticmethod
    def get_snapshot_at_or_before(
        frames,
        target_ms,
    ):

        eligible = [
            frame
            for frame in frames
            if frame.timestamp_ms <= target_ms
        ]

        if not eligible:
            return None

        return eligible[-1]

    @staticmethod
    def get_death_count(
        events,
        participant_id,
        start_ms,
        end_ms,
    ):

        return sum(
            1
            for event in events
            if event.event_type == "CHAMPION_KILL"
            and event.victim_id == participant_id
            and start_ms < event.timestamp_ms <= end_ms
        )

    def calculate_phase(
        self,
        frames,
        events,
        participant_id,
        phase_name,
        start_minute,
        end_minute,
    ):

        start_ms = int(start_minute * 60_000)
        end_ms = int(end_minute * 60_000)

        start_frame = self.get_snapshot_at_or_before(
            frames,
            start_ms,
        )

        end_frame = self.get_snapshot_at_or_before(
            frames,
            end_ms,
        )

        start_cs = self.get_frame_cs(start_frame)
        end_cs = self.get_frame_cs(end_frame)

        if start_cs is None or end_cs is None:
            cs_gained = None
        else:
            cs_gained = max(0, end_cs - start_cs)

        actual_start_minute = (
            start_frame.timestamp_ms / 60_000
            if start_frame is not None
            else None
        )

        actual_end_minute = (
            end_frame.timestamp_ms / 60_000
            if end_frame is not None
            else None
        )

        if (
            cs_gained is not None
            and actual_start_minute is not None
            and actual_end_minute is not None
        ):

            elapsed_minutes = (
                actual_end_minute - actual_start_minute
            )

            cs_per_minute = self.safe_divide(
                cs_gained,
                elapsed_minutes,
            )

        else:
            cs_per_minute = None

        deaths = self.get_death_count(
            events=events,
            participant_id=participant_id,
            start_ms=start_ms,
            end_ms=end_ms,
        )

        return PhasePerformance(
            phase=phase_name,
            start_minute=start_minute,
            end_minute=end_minute,
            cs_gained=cs_gained,
            cs_per_minute=(
                round(cs_per_minute, 2)
                if cs_per_minute is not None
                else None
            ),
            deaths=deaths,
        )

    @staticmethod
    def calculate_rate_change(
        previous_rate,
        current_rate,
    ):

        if (
            previous_rate is None
            or current_rate is None
            or previous_rate <= 0
        ):
            return None

        return round(
            (
                (current_rate - previous_rate)
                / previous_rate
            ) * 100,
            2,
        )

    def get_player_timeline_overview(
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

            return TimelinePlayerOverview(
                riot_account_id=riot_account.id,
                puuid=riot_account.puuid,
                total_matches=0,

                average_early_cs_per_minute=None,
                average_mid_cs_per_minute=None,
                average_late_cs_per_minute=None,

                average_early_deaths=0,
                average_mid_deaths=0,
                average_late_deaths=0,

                matches=[],
            )

        match_ids = [
            record["match"].id
            for record in records
        ]

        all_frames = self.repository.get_timeline_frames(
            match_ids
        )

        all_events = self.repository.get_timeline_events(
            match_ids
        )

        frames_by_match_participant = {}

        for frame in all_frames:

            key = (
                frame.match_id,
                frame.participant_id,
            )

            frames_by_match_participant.setdefault(
                key,
                [],
            ).append(frame)

        events_by_match = {}

        for event in all_events:

            events_by_match.setdefault(
                event.match_id,
                [],
            ).append(event)

        performances = []

        for record in records:

            match = record["match"]
            player = record["player"]

            duration_minutes = (
                (match.game_duration or 0) / 60
            )

            if duration_minutes <= 0:
                continue

            key = (
                match.id,
                player.participant_id,
            )

            frames = frames_by_match_participant.get(
                key,
                [],
            )

            events = events_by_match.get(
                match.id,
                [],
            )

            if not frames:
                continue

            early_end = min(
                self.EARLY_END,
                duration_minutes,
            )

            mid_end = min(
                self.MID_END,
                duration_minutes,
            )

            early = self.calculate_phase(
                frames,
                events,
                player.participant_id,
                "early",
                0,
                early_end,
            )

            mid = self.calculate_phase(
                frames,
                events,
                player.participant_id,
                "mid",
                early_end,
                mid_end,
            )

            late = self.calculate_phase(
                frames,
                events,
                player.participant_id,
                "late",
                mid_end,
                duration_minutes,
            )

            performance = MatchTimelinePerformance(
                match_id=match.match_id,
                game_version=match.game_version,

                champion_name=player.champion_name,
                role=player.role,

                game_duration_minutes=round(
                    duration_minutes,
                    2,
                ),

                early_game=early,
                mid_game=mid,
                late_game=late,

                cs_rate_change_mid_vs_early=(
                    self.calculate_rate_change(
                        early.cs_per_minute,
                        mid.cs_per_minute,
                    )
                ),

                cs_rate_change_late_vs_mid=(
                    self.calculate_rate_change(
                        mid.cs_per_minute,
                        late.cs_per_minute,
                    )
                ),
            )

            performances.append(performance)

        return TimelinePlayerOverview(
            riot_account_id=riot_account.id,
            puuid=riot_account.puuid,

            total_matches=len(performances),

            average_early_cs_per_minute=self.average(
                [
                    m.early_game.cs_per_minute
                    for m in performances
                ]
            ),

            average_mid_cs_per_minute=self.average(
                [
                    m.mid_game.cs_per_minute
                    for m in performances
                ]
            ),

            average_late_cs_per_minute=self.average(
                [
                    m.late_game.cs_per_minute
                    for m in performances
                ]
            ),

            average_early_deaths=self.average(
                [
                    m.early_game.deaths
                    for m in performances
                ]
            ) or 0,

            average_mid_deaths=self.average(
                [
                    m.mid_game.deaths
                    for m in performances
                ]
            ) or 0,

            average_late_deaths=self.average(
                [
                    m.late_game.deaths
                    for m in performances
                ]
            ) or 0,

            matches=performances,
        )