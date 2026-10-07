
from app.repositories.analytics_repository import AnalyticsRepository


class ContextualFarmingService:

    # Timeline frames are normally approximately 60 seconds apart.
    MIN_INTERVAL_MS = 30_000
    MAX_INTERVAL_MS = 120_000

    OBJECTIVE_EVENT_TYPES = {
        "ELITE_MONSTER_KILL",
        "BUILDING_KILL",
        "TURRET_PLATE_DESTROYED",
    }

    def __init__(self, db):
        self.repository = AnalyticsRepository(db)

    @staticmethod
    def _safe_delta(current, previous):
        """
        Return a counter difference only when both values exist
        and the counter has not decreased.
        """

        if current is None or previous is None:
            return None

        delta = current - previous

        if delta < 0:
            return None

        return delta

    @staticmethod
    def _get_total_cs(frame):
        if frame is None:
            return None

        lane_cs = frame.minions_killed
        jungle_cs = frame.jungle_minions_killed

        if lane_cs is None and jungle_cs is None:
            return None

        return (lane_cs or 0) + (jungle_cs or 0)

    @staticmethod
    def _get_event_assists(event):
        raw_data = event.raw_data or {}

        assists = raw_data.get(
            "assistingParticipantIds",
            [],
        )

        if not isinstance(assists, list):
            return []

        return assists

    @staticmethod
    def _get_event_killer(event):
        raw_data = event.raw_data or {}

        return (
            event.killer_id
            or raw_data.get("killerId")
        )

    @staticmethod
    def _is_player_in_event(
        event,
        participant_id,
    ):
        """
        Identify direct player participation.

        Team-wide events without player attribution are
        intentionally excluded.
        """

        if event.event_type == "CHAMPION_KILL":

            return (
                event.killer_id == participant_id
                or event.victim_id == participant_id
                or participant_id in (
                    ContextualFarmingService._get_event_assists(
                        event
                    )
                )
            )

        if event.event_type in (
            ContextualFarmingService.OBJECTIVE_EVENT_TYPES
        ):

            return (
                ContextualFarmingService._get_event_killer(
                    event
                ) == participant_id
                or participant_id in (
                    ContextualFarmingService._get_event_assists(
                        event
                    )
                )
                or event.participant_id == participant_id
            )

        return False

    @staticmethod
    def _get_event_counts(
        events,
        participant_id,
        start_ms,
        end_ms,
    ):

        counts = {
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "objective_participations": 0,
            "dragon_participations": 0,
            "building_participations": 0,
            "turret_plate_participations": 0,
        }

        for event in events:

            if not (
                start_ms < event.timestamp_ms <= end_ms
            ):
                continue

            event_type = event.event_type

            if event_type == "CHAMPION_KILL":

                if event.killer_id == participant_id:
                    counts["kills"] += 1

                if event.victim_id == participant_id:
                    counts["deaths"] += 1

                if participant_id in (
                    ContextualFarmingService._get_event_assists(
                        event
                    )
                ):
                    counts["assists"] += 1

            elif event_type in (
                ContextualFarmingService.OBJECTIVE_EVENT_TYPES
            ):

                if not ContextualFarmingService._is_player_in_event(
                    event,
                    participant_id,
                ):
                    continue

                counts["objective_participations"] += 1

                raw_data = event.raw_data or {}

                if (
                    event_type == "ELITE_MONSTER_KILL"
                    and raw_data.get("monsterType") == "DRAGON"
                ):
                    counts["dragon_participations"] += 1

                elif event_type == "BUILDING_KILL":
                    counts["building_participations"] += 1

                elif event_type == "TURRET_PLATE_DESTROYED":
                    counts["turret_plate_participations"] += 1

        return counts

    def _extract_match_intervals(
        self,
        match,
        player,
        frames,
        events,
    ):

        frames = sorted(
            frames,
            key=lambda frame: frame.timestamp_ms,
        )

        events = sorted(
            events,
            key=lambda event: event.timestamp_ms,
        )

        intervals = []
        skipped_intervals = []

        for index in range(1, len(frames)):

            previous = frames[index - 1]
            current = frames[index]

            start_ms = previous.timestamp_ms
            end_ms = current.timestamp_ms

            elapsed_ms = end_ms - start_ms

            if elapsed_ms < self.MIN_INTERVAL_MS:

                skipped_intervals.append({
                    "reason": "interval_too_short",
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "elapsed_ms": elapsed_ms,
                })

                continue

            if elapsed_ms > self.MAX_INTERVAL_MS:

                skipped_intervals.append({
                    "reason": "interval_too_long",
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "elapsed_ms": elapsed_ms,
                })

                continue

            previous_cs = self._get_total_cs(previous)
            current_cs = self._get_total_cs(current)

            cs_delta = self._safe_delta(
                current_cs,
                previous_cs,
            )

            lane_cs_delta = self._safe_delta(
                current.minions_killed,
                previous.minions_killed,
            )

            jungle_cs_delta = self._safe_delta(
                current.jungle_minions_killed,
                previous.jungle_minions_killed,
            )

            gold_delta = self._safe_delta(
                current.total_gold,
                previous.total_gold,
            )

            xp_delta = self._safe_delta(
                current.xp,
                previous.xp,
            )

            elapsed_minutes = elapsed_ms / 60_000

            cs_per_minute = (
                round(cs_delta / elapsed_minutes, 2)
                if cs_delta is not None
                else None
            )

            interval_events = self._get_event_counts(
                events=events,
                participant_id=player.participant_id,
                start_ms=start_ms,
                end_ms=end_ms,
            )

            intervals.append({

                "match_id": match.match_id,
                "game_version": match.game_version,

                "champion": player.champion_name,
                "role": player.role,
                "participant_id": player.participant_id,

                "start_minute": round(
                    start_ms / 60_000,
                    2,
                ),

                "end_minute": round(
                    end_ms / 60_000,
                    2,
                ),

                "elapsed_seconds": round(
                    elapsed_ms / 1000,
                    2,
                ),

                "cs_start": previous_cs,
                "cs_end": current_cs,

                "cs_delta": cs_delta,
                "lane_cs_delta": lane_cs_delta,
                "jungle_cs_delta": jungle_cs_delta,

                "cs_per_minute": cs_per_minute,

                "gold_delta": gold_delta,
                "xp_delta": xp_delta,

                "level_start": previous.level,
                "level_end": current.level,

                "data_quality": {
                    "valid_cs_delta": cs_delta is not None,
                    "valid_gold_delta": gold_delta is not None,
                    "valid_xp_delta": xp_delta is not None,
                },

                "events": interval_events,
            })

        return intervals, skipped_intervals

    def extract_match_intervals(
        self,
        match,
        player,
        frames,
        events,
    ):
        """
        Public reusable interface for extracting contextual
        intervals for a single participant in a single match.

        This does not write to the database.
        """

        return self._extract_match_intervals(
            match=match,
            player=player,
            frames=frames,
            events=events,
        )

    def get_player_interval_features(
        self,
        riot_account_id: int,
        limit: int = 10,
    ):

        account_data = self.repository.get_riot_account(
            riot_account_id
        )

        if account_data is None:
            return None

        riot_account, league_profile = account_data

        records = self.repository.get_player_matches(
            puuid=riot_account.puuid,
            limit=limit,
        )

        if not records:

            return {
                "riot_account_id": riot_account_id,
                "matches_analyzed": 0,
                "total_intervals": 0,
                "intervals": [],
                "skipped_intervals": [],
            }

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

        all_intervals = []
        all_skipped_intervals = []

        matches_with_frames = 0

        for record in records:

            match = record["match"]
            player = record["player"]

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

            if len(frames) < 2:
                continue

            matches_with_frames += 1

            intervals, skipped = self._extract_match_intervals(
                match=match,
                player=player,
                frames=frames,
                events=events,
            )

            all_intervals.extend(intervals)
            all_skipped_intervals.extend(skipped)

        return {
            "riot_account_id": riot_account_id,
            "matches_analyzed": matches_with_frames,
            "total_intervals": len(all_intervals),
            "intervals": all_intervals,
            "skipped_intervals": all_skipped_intervals,
        }