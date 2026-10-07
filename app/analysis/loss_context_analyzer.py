class LossContextAnalyzer:

    EARLY_CHECKPOINT_MS = (
        10 * 60 * 1000
    )

    MID_CHECKPOINT_MS = (
        20 * 60 * 1000
    )

    @staticmethod
    def _latest_frame_before(
        frames,
        timestamp_ms,
    ):

        latest = None

        for frame in frames:

            if (
                frame.timestamp_ms
                > timestamp_ms
            ):
                break

            latest = frame

        return latest

    @staticmethod
    def _build_frames_map(
        frames,
    ):

        result = {}

        for frame in frames:

            result.setdefault(
                frame.participant_id,
                [],
            ).append(
                frame
            )

        for player_frames in (
            result.values()
        ):

            player_frames.sort(
                key=lambda frame:
                    frame.timestamp_ms
            )

        return result

    def _team_state(
        self,
        participants,
        frames_by_participant,
        timestamp_ms,
    ):

        state = {
            100: {
                "gold": 0,
                "levels": 0,
                "players": 0,
            },

            200: {
                "gold": 0,
                "levels": 0,
                "players": 0,
            },
        }

        for participant in participants:

            if (
                participant.team_id
                not in state
            ):
                continue

            frames = (
                frames_by_participant.get(
                    participant.participant_id,
                    [],
                )
            )

            frame = (
                self._latest_frame_before(
                    frames,
                    timestamp_ms,
                )
            )

            if frame is None:
                continue

            bucket = state[
                participant.team_id
            ]

            bucket["gold"] += (
                frame.total_gold
                or 0
            )

            bucket["levels"] += (
                frame.level
                or 0
            )

            bucket["players"] += 1

        return state

    @staticmethod
    def _difference(
        state,
        team_id,
        field,
    ):

        enemy_team_id = (
            200
            if team_id == 100
            else 100
        )

        return (
            state[
                team_id
            ][field]
            - state[
                enemy_team_id
            ][field]
        )

    def _team_trajectory(
        self,
        player,
        participants,
        frames,
    ):

        frames_by_participant = (
            self._build_frames_map(
                frames
            )
        )

        if not frames:
            return {}

        final_timestamp = max(
            frame.timestamp_ms
            for frame in frames
        )

        checkpoints = {
            "minute_10":
                min(
                    self.EARLY_CHECKPOINT_MS,
                    final_timestamp,
                ),

            "minute_20":
                min(
                    self.MID_CHECKPOINT_MS,
                    final_timestamp,
                ),

            "final":
                final_timestamp,
        }

        result = {}

        for name, timestamp in (
            checkpoints.items()
        ):

            state = (
                self._team_state(
                    participants=
                        participants,
                    frames_by_participant=
                        frames_by_participant,
                    timestamp_ms=
                        timestamp,
                )
            )

            result[
                name
            ] = {
                "timestamp_ms":
                    timestamp,

                "gold_difference":
                    self._difference(
                        state,
                        player.team_id,
                        "gold",
                    ),

                "level_difference":
                    self._difference(
                        state,
                        player.team_id,
                        "levels",
                    ),
            }

        return result

    @staticmethod
    def _player_team_rank(
        player,
        participants,
    ):
        """
        Raw within-team ranking.

        Useful as contextual evidence,
        NOT a role-adjusted performance score.
        """

        teammates = [
            participant
            for participant in participants
            if (
                participant.team_id
                == player.team_id
            )
        ]

        gold_sorted = sorted(
            teammates,
            key=lambda p:
                (
                    p.gold_earned
                    or p.total_gold
                    or 0
                ),
            reverse=True,
        )

        damage_sorted = sorted(
            teammates,
            key=lambda p:
                (
                    getattr(
                        p,
                        "total_damage_dealt_to_champions",
                        0,
                    )
                    or 0
                ),
            reverse=True,
        )

        def rank_of(
            collection,
        ):

            for index, participant in enumerate(
                collection,
                start=1,
            ):

                if (
                    participant.participant_id
                    == player.participant_id
                ):
                    return index

            return None

        return {
            "gold_rank_on_team":
                rank_of(
                    gold_sorted
                ),

            "damage_rank_on_team":
                rank_of(
                    damage_sorted
                ),

            "team_size":
                len(
                    teammates
                ),
        }

    @staticmethod
    def _critical_summary(
        critical_moments,
    ):

        severe = [
            moment
            for moment in critical_moments
            if (
                moment.get(
                    "severity",
                    0,
                )
                >= 4
            )
        ]

        total_impact = sum(
            moment.get(
                "severity",
                0,
            )
            for moment
            in critical_moments
        )

        return {
            "negative_moment_count":
                len(
                    critical_moments
                ),

            "high_impact_negative_count":
                len(
                    severe
                ),

            "negative_impact_total":
                total_impact,
        }

    @staticmethod
    def _positive_summary(
        positive_moments,
    ):

        total_impact = sum(
            moment.get(
                "impact_score",
                0,
            )
            for moment
            in positive_moments
        )

        objective_conversions = sum(
            1
            for moment in positive_moments
            if (
                "objective_conversion"
                in moment.get(
                    "reasons",
                    []
                )
            )
        )

        return {
            "positive_moment_count":
                len(
                    positive_moments
                ),

            "positive_impact_total":
                total_impact,

            "objective_conversions":
                objective_conversions,
        }

    def _classification(
        self,
        player,
        team_rank,
        critical,
        positive,
        trajectory,
    ):
        """
        MVP heuristic classification.

        This is deliberately NOT presented as
        a causal truth or validated performance score.
        """

        if player.win:

            return {
                "type":
                    "WIN",

                "confidence":
                    "NOT_APPLICABLE",
            }

        positive_indicators = 0
        negative_indicators = 0

        gold_rank = (
            team_rank.get(
                "gold_rank_on_team"
            )
        )

        damage_rank = (
            team_rank.get(
                "damage_rank_on_team"
            )
        )

        if (
            gold_rank is not None
            and gold_rank <= 2
        ):
            positive_indicators += 1

        if (
            damage_rank is not None
            and damage_rank <= 2
        ):
            positive_indicators += 1

        if (
            positive[
                "positive_impact_total"
            ]
            >
            critical[
                "negative_impact_total"
            ]
        ):
            positive_indicators += 1

        if (
            positive[
                "objective_conversions"
            ]
            >= 1
        ):
            positive_indicators += 1

        if (
            critical[
                "high_impact_negative_count"
            ]
            >= 2
        ):
            negative_indicators += 2

        elif (
            critical[
                "high_impact_negative_count"
            ]
            == 1
        ):
            negative_indicators += 1

        final_state = (
            trajectory.get(
                "final",
                {}
            )
        )

        final_gold_gap = (
            final_state.get(
                "gold_difference",
                0,
            )
        )

        if (
            final_gold_gap
            <= -3000
        ):
            team_collapse = True

        else:
            team_collapse = False

        if (
            positive_indicators >= 3
            and
            negative_indicators <= 1
            and
            team_collapse
        ):

            classification = (
                "STRONG_INDIVIDUAL_INDICATORS_IN_LOSS"
            )

        elif (
            negative_indicators >= 2
        ):

            classification = (
                "SIGNIFICANT_INDIVIDUAL_MISTAKES_IN_LOSS"
            )

        else:

            classification = (
                "MIXED_LOSS_CONTEXT"
            )

        return {
            "type":
                classification,

            "positive_indicators":
                positive_indicators,

            "negative_indicators":
                negative_indicators,

            "team_finished_heavily_behind":
                team_collapse,
        }

    def _opportunities(
        self,
        critical_moments,
    ):

        opportunities = []

        for moment in sorted(
            critical_moments,
            key=lambda item:
                item.get(
                    "severity",
                    0,
                ),
            reverse=True,
        ):

            reasons = set(
                moment.get(
                    "reasons",
                    []
                )
            )

            if (
                "enemy_objective_after_death"
                in reasons
            ):

                objective = (
                    moment.get(
                        "next_major_objective"
                    )
                    or {}
                )

                opportunities.append({
                    "minute":
                        moment.get(
                            "minute"
                        ),

                    "type":
                        "OBJECTIVE_SURVIVAL",

                    "title":
                        "Stay alive before major objective windows",

                    "evidence": {
                        "objective":
                            objective.get(
                                "objective"
                            ),

                        "seconds_after_death":
                            objective.get(
                                "seconds_after_death"
                            ),
                    },
                })

            elif (
                "local_number_disadvantage"
                in reasons
            ):

                opportunities.append({
                    "minute":
                        moment.get(
                            "minute"
                        ),

                    "type":
                        "FIGHT_SELECTION",

                    "title":
                        "Avoid locally outnumbered engagements",

                    "evidence":
                        moment.get(
                            "local_fight_context",
                            {},
                        ),
                })

            elif (
                "team_level_disadvantage"
                in reasons
                or
                "team_gold_disadvantage"
                in reasons
            ):

                opportunities.append({
                    "minute":
                        moment.get(
                            "minute"
                        ),

                    "type":
                        "FIGHT_SELECTION",

                    "title":
                        "Choose a higher-percentage fight",

                    "evidence":
                        moment.get(
                            "before",
                            {},
                        ),
                })

            if (
                len(
                    opportunities
                )
                >= 3
            ):
                break

        return opportunities

    def analyze(
        self,
        player,
        participants,
        frames,
        critical_moments,
        positive_moments,
    ):

        trajectory = (
            self._team_trajectory(
                player=player,
                participants=
                    participants,
                frames=frames,
            )
        )

        team_rank = (
            self._player_team_rank(
                player=player,
                participants=
                    participants,
            )
        )

        critical = (
            self._critical_summary(
                critical_moments
            )
        )

        positive = (
            self._positive_summary(
                positive_moments
            )
        )

        classification = (
            self._classification(
                player=player,
                team_rank=
                    team_rank,
                critical=
                    critical,
                positive=
                    positive,
                trajectory=
                    trajectory,
            )
        )

        opportunities = (
            self._opportunities(
                critical_moments
            )
        )

        return {
            "result":
                (
                    "WIN"
                    if player.win
                    else "LOSS"
                ),

            "classification":
                classification,

            "team_trajectory":
                trajectory,

            "player_team_context":
                team_rank,

            "positive_summary":
                positive,

            "negative_summary":
                critical,

            "highest_leverage_opportunities":
                opportunities,

            "important_note":
                (
                    "This analysis describes "
                    "performance indicators and "
                    "team context. It does not "
                    "prove which player caused "
                    "the match result."
                ),
        }