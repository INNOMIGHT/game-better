from math import hypot


class CriticalMomentAnalyzer:

    POST_EVENT_WINDOW_MS = 90_000

    # Death shortly before a major objective.
    OBJECTIVE_LOOKAHEAD_MS = 90_000

    IMPORTANT_GOLD_GAP = 1000
    IMPORTANT_LEVEL_GAP = 2
    LARGE_GOLD_SWING = 800

    # Approximate local fight radius.
    #
    # This is a heuristic, not Riot-defined.
    LOCAL_FIGHT_RADIUS = 2500

    # Timeline position snapshots are roughly
    # one minute apart. Don't use very stale
    # positions for local-player counting.
    MAX_POSITION_AGE_MS = 75_000

    MAJOR_MONSTERS = {
        "DRAGON",
        "BARON_NASHOR",
        "RIFTHERALD",
    }

    # --------------------------------------------------
    # BASIC HELPERS
    # --------------------------------------------------

    @staticmethod
    def _total_cs(frame):

        if frame is None:
            return 0

        return (
            (frame.minions_killed or 0)
            + (frame.jungle_minions_killed or 0)
        )

    @staticmethod
    def _latest_frame_before(
        frames,
        timestamp_ms,
    ):

        latest = None

        for frame in frames:

            if frame.timestamp_ms > timestamp_ms:
                break

            latest = frame

        return latest

    @staticmethod
    def _extract_position(frame):

        if frame is None:
            return None

        x = getattr(
            frame,
            "position_x",
            None,
        )

        y = getattr(
            frame,
            "position_y",
            None,
        )

        if (
            x is None
            or y is None
        ):
            return None

        return (
            float(x),
            float(y),
        )

    @staticmethod
    def _build_frames_map(
        frames,
    ):

        result = {}

        for frame in frames:

            result.setdefault(
                frame.participant_id,
                [],
            ).append(frame)

        for participant_frames in (
            result.values()
        ):

            participant_frames.sort(
                key=lambda frame:
                    frame.timestamp_ms
            )

        return result

    # --------------------------------------------------
    # TEAM STATE
    # --------------------------------------------------

    def _team_state_at(
        self,
        participants,
        frames_by_participant,
        timestamp_ms,
    ):

        states = {
            100: {
                "gold": 0,
                "xp": 0,
                "levels": 0,
                "cs": 0,
                "players_found": 0,
            },

            200: {
                "gold": 0,
                "xp": 0,
                "levels": 0,
                "cs": 0,
                "players_found": 0,
            },
        }

        for participant in participants:

            team_id = (
                participant.team_id
            )

            if team_id not in states:
                continue

            player_frames = (
                frames_by_participant.get(
                    participant.participant_id,
                    [],
                )
            )

            frame = (
                self._latest_frame_before(
                    player_frames,
                    timestamp_ms,
                )
            )

            if frame is None:
                continue

            team = states[
                team_id
            ]

            team["gold"] += (
                frame.total_gold or 0
            )

            team["xp"] += (
                frame.xp or 0
            )

            team["levels"] += (
                frame.level or 0
            )

            team["cs"] += (
                self._total_cs(
                    frame
                )
            )

            team[
                "players_found"
            ] += 1

        return states

    @staticmethod
    def _team_difference(
        states,
        player_team_id,
        metric,
    ):

        opponent_team_id = (
            200
            if player_team_id == 100
            else 100
        )

        return (
            states[
                player_team_id
            ][metric]
            - states[
                opponent_team_id
            ][metric]
        )

    # --------------------------------------------------
    # LOCAL PLAYER COUNT
    # --------------------------------------------------

    def _local_numbers_at(
        self,
        player,
        participants,
        frames_by_participant,
        timestamp_ms,
    ):
        """
        Approximate how many allies/enemies were near
        the player using the latest timeline position
        snapshot available before the event.

        This is intentionally marked approximate because
        Riot timeline frames are not continuous tracking.
        """

        player_frames = (
            frames_by_participant.get(
                player.participant_id,
                [],
            )
        )

        player_frame = (
            self._latest_frame_before(
                player_frames,
                timestamp_ms,
            )
        )

        if player_frame is None:

            return {
                "available": False,
            }

        player_age = (
            timestamp_ms
            - player_frame.timestamp_ms
        )

        if (
            player_age
            > self.MAX_POSITION_AGE_MS
        ):

            return {
                "available": False,
            }

        player_position = (
            self._extract_position(
                player_frame
            )
        )

        if player_position is None:

            return {
                "available": False,
            }

        player_x, player_y = (
            player_position
        )

        nearby_allies = 0
        nearby_enemies = 0

        nearby_players = []

        for participant in participants:

            participant_frames = (
                frames_by_participant.get(
                    participant.participant_id,
                    [],
                )
            )

            frame = (
                self._latest_frame_before(
                    participant_frames,
                    timestamp_ms,
                )
            )

            if frame is None:
                continue

            frame_age = (
                timestamp_ms
                - frame.timestamp_ms
            )

            if (
                frame_age
                > self.MAX_POSITION_AGE_MS
            ):
                continue

            position = (
                self._extract_position(
                    frame
                )
            )

            if position is None:
                continue

            x, y = position

            distance = hypot(
                x - player_x,
                y - player_y,
            )

            if (
                distance
                > self.LOCAL_FIGHT_RADIUS
            ):
                continue

            is_ally = (
                participant.team_id
                == player.team_id
            )

            if is_ally:
                nearby_allies += 1

            else:
                nearby_enemies += 1

            nearby_players.append({
                "participant_id":
                    participant.participant_id,

                "team_id":
                    participant.team_id,

                "distance":
                    round(
                        distance,
                        1,
                    ),
            })

        number_difference = (
            nearby_allies
            - nearby_enemies
        )

        return {
            "available": True,

            # Includes the player.
            "nearby_allies":
                nearby_allies,

            "nearby_enemies":
                nearby_enemies,

            "number_difference":
                number_difference,

            "outnumbered":
                number_difference < 0,

            "nearby_players":
                nearby_players,
        }

    # --------------------------------------------------
    # OBJECTIVE CONTEXT
    # --------------------------------------------------

    @staticmethod
    def _objective_name(
        event,
    ):

        raw = (
            event.raw_data
            or {}
        )

        monster_type = (
            raw.get(
                "monsterType"
            )
        )

        monster_sub_type = (
            raw.get(
                "monsterSubType"
            )
        )

        if (
            monster_type
            == "DRAGON"
        ):

            return (
                monster_sub_type
                or "DRAGON"
            )

        if (
            monster_type
            == "BARON_NASHOR"
        ):

            return "BARON"

        if (
            monster_type
            == "RIFTHERALD"
        ):

            return "RIFT_HERALD"

        return monster_type

    def _objective_after_death(
        self,
        death_timestamp_ms,
        player_team_id,
        events,
    ):

        enemy_team_id = (
            200
            if player_team_id == 100
            else 100
        )

        window_end = (
            death_timestamp_ms
            + self.OBJECTIVE_LOOKAHEAD_MS
        )

        candidates = []

        for event in events:

            if (
                event.timestamp_ms
                <= death_timestamp_ms
            ):
                continue

            if (
                event.timestamp_ms
                > window_end
            ):
                break

            if (
                event.event_type
                != "ELITE_MONSTER_KILL"
            ):
                continue

            raw = (
                event.raw_data
                or {}
            )

            monster_type = (
                raw.get(
                    "monsterType"
                )
            )

            if (
                monster_type
                not in self.MAJOR_MONSTERS
            ):
                continue

            killer_team_id = (
                event.team_id
                or raw.get(
                    "killerTeamId"
                )
            )

            objective = {
                "objective":
                    self._objective_name(
                        event
                    ),

                "timestamp_ms":
                    event.timestamp_ms,

                "seconds_after_death":
                    round(
                        (
                            event.timestamp_ms
                            - death_timestamp_ms
                        )
                        / 1000,
                        1,
                    ),

                "team_id":
                    killer_team_id,

                "taken_by_enemy":
                    (
                        killer_team_id
                        == enemy_team_id
                    ),
            }

            candidates.append(
                objective
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item:
                item["timestamp_ms"]
        )

        return candidates[0]

    # --------------------------------------------------
    # DEATH ANALYSIS
    # --------------------------------------------------

    def _analyze_player_death(
        self,
        event,
        player,
        participants,
        frames_by_participant,
        events,
    ):

        timestamp_ms = (
            event.timestamp_ms
        )

        before = (
            self._team_state_at(
                participants=
                    participants,
                frames_by_participant=
                    frames_by_participant,
                timestamp_ms=
                    timestamp_ms,
            )
        )

        after_timestamp = (
            timestamp_ms
            + self.POST_EVENT_WINDOW_MS
        )

        after = (
            self._team_state_at(
                participants=
                    participants,
                frames_by_participant=
                    frames_by_participant,
                timestamp_ms=
                    after_timestamp,
            )
        )

        team_id = (
            player.team_id
        )

        gold_before = (
            self._team_difference(
                before,
                team_id,
                "gold",
            )
        )

        gold_after = (
            self._team_difference(
                after,
                team_id,
                "gold",
            )
        )

        level_before = (
            self._team_difference(
                before,
                team_id,
                "levels",
            )
        )

        level_after = (
            self._team_difference(
                after,
                team_id,
                "levels",
            )
        )

        gold_swing = (
            gold_after
            - gold_before
        )

        level_swing = (
            level_after
            - level_before
        )

        local_numbers = (
            self._local_numbers_at(
                player=player,
                participants=
                    participants,
                frames_by_participant=
                    frames_by_participant,
                timestamp_ms=
                    timestamp_ms,
            )
        )

        next_objective = (
            self._objective_after_death(
                death_timestamp_ms=
                    timestamp_ms,
                player_team_id=
                    team_id,
                events=events,
            )
        )

        reasons = []

        severity = 1

        # ----------------------------------
        # GLOBAL TEAM DISADVANTAGE
        # ----------------------------------

        if (
            gold_before
            <= -self.IMPORTANT_GOLD_GAP
        ):

            reasons.append(
                "team_gold_disadvantage"
            )

            severity += 1

        if (
            level_before
            <= -self.IMPORTANT_LEVEL_GAP
        ):

            reasons.append(
                "team_level_disadvantage"
            )

            severity += 1

        # ----------------------------------
        # LOCAL NUMBER DISADVANTAGE
        # ----------------------------------

        if (
            local_numbers.get(
                "available"
            )
            and
            local_numbers.get(
                "outnumbered"
            )
        ):

            reasons.append(
                "local_number_disadvantage"
            )

            severity += 1

        # ----------------------------------
        # AFTERMATH
        # ----------------------------------

        if (
            gold_swing
            <= -self.LARGE_GOLD_SWING
        ):

            reasons.append(
                "gap_widened_after_death"
            )

            severity += 2

        if (
            level_swing < 0
        ):

            reasons.append(
                "level_gap_widened"
            )

            severity += 1

        # ----------------------------------
        # OBJECTIVE CONSEQUENCE
        # ----------------------------------

        if (
            next_objective
            and
            next_objective[
                "taken_by_enemy"
            ]
        ):

            reasons.append(
                "enemy_objective_after_death"
            )

            severity += 2

        minute = (
            timestamp_ms
            / 60_000
        )

        return {
            "type":
                "PLAYER_DEATH",

            "minute":
                round(
                    minute,
                    2,
                ),

            "timestamp_ms":
                timestamp_ms,

            "severity":
                min(
                    severity,
                    5,
                ),

            "reasons":
                reasons,

            "before": {
                "team_gold_difference":
                    gold_before,

                "team_level_difference":
                    level_before,
            },

            "local_fight_context":
                local_numbers,

            "next_major_objective":
                next_objective,

            "after_90_seconds": {
                "team_gold_difference":
                    gold_after,

                "team_level_difference":
                    level_after,
            },

            "change": {
                "gold_difference_change":
                    gold_swing,

                "level_difference_change":
                    level_swing,
            },
        }

    # --------------------------------------------------
    # PUBLIC ANALYSIS
    # --------------------------------------------------

    def analyze(
        self,
        player,
        participants,
        frames,
        events,
    ):

        frames_by_participant = (
            self._build_frames_map(
                frames
            )
        )

        sorted_events = sorted(
            events,
            key=lambda event:
                event.timestamp_ms,
        )

        critical_moments = []

        for event in sorted_events:

            if (
                event.event_type
                != "CHAMPION_KILL"
            ):
                continue

            if (
                event.victim_id
                != player.participant_id
            ):
                continue

            moment = (
                self._analyze_player_death(
                    event=event,
                    player=player,
                    participants=
                        participants,
                    frames_by_participant=
                        frames_by_participant,
                    events=
                        sorted_events,
                )
            )

            critical_moments.append(
                moment
            )

        critical_moments.sort(
            key=lambda item: (
                -item["severity"],
                item["timestamp_ms"],
            )
        )

        return {
            "critical_moment_count":
                len(
                    critical_moments
                ),

            "critical_moments":
                critical_moments,
        }