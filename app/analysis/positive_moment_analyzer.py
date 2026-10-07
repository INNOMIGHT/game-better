class PositiveMomentAnalyzer:

    OBJECTIVE_LOOKAHEAD_MS = 90_000

    MAJOR_MONSTERS = {
        "DRAGON",
        "BARON_NASHOR",
        "RIFTHERALD",
    }

    @staticmethod
    def _get_assists(
        event,
    ):

        raw = (
            event.raw_data
            or {}
        )

        assists = raw.get(
            "assistingParticipantIds",
            [],
        )

        if not isinstance(
            assists,
            list,
        ):
            return []

        return assists

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

        if monster_type == "DRAGON":

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

    def _objective_after_event(
        self,
        timestamp_ms,
        player_team_id,
        events,
    ):

        end_ms = (
            timestamp_ms
            + self.OBJECTIVE_LOOKAHEAD_MS
        )

        for event in events:

            if (
                event.timestamp_ms
                <= timestamp_ms
            ):
                continue

            if (
                event.timestamp_ms
                > end_ms
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

            if (
                killer_team_id
                != player_team_id
            ):
                continue

            return {
                "objective":
                    self._objective_name(
                        event
                    ),

                "timestamp_ms":
                    event.timestamp_ms,

                "seconds_after":
                    round(
                        (
                            event.timestamp_ms
                            - timestamp_ms
                        )
                        / 1000,
                        1,
                    ),
            }

        return None

    def analyze(
        self,
        player,
        events,
    ):

        events = sorted(
            events,
            key=lambda event:
                event.timestamp_ms,
        )

        positive_moments = []

        for event in events:

            if (
                event.event_type
                != "CHAMPION_KILL"
            ):
                continue

            player_kill = (
                event.killer_id
                == player.participant_id
            )

            player_assist = (
                player.participant_id
                in self._get_assists(
                    event
                )
            )

            if not (
                player_kill
                or player_assist
            ):
                continue

            objective = (
                self._objective_after_event(
                    timestamp_ms=
                        event.timestamp_ms,
                    player_team_id=
                        player.team_id,
                    events=events,
                )
            )

            impact_score = 1

            reasons = []

            if player_kill:

                reasons.append(
                    "player_kill"
                )

                impact_score += 1

            if player_assist:

                reasons.append(
                    "player_assist"
                )

            if objective:

                reasons.append(
                    "objective_conversion"
                )

                impact_score += 2

            minute = (
                event.timestamp_ms
                / 60_000
            )

            positive_moments.append({
                "type":
                    "POSITIVE_COMBAT_EVENT",

                "minute":
                    round(
                        minute,
                        2,
                    ),

                "timestamp_ms":
                    event.timestamp_ms,

                "impact_score":
                    min(
                        impact_score,
                        5,
                    ),

                "reasons":
                    reasons,

                "objective_conversion":
                    objective,
            })

        positive_moments.sort(
            key=lambda item: (
                -item[
                    "impact_score"
                ],
                item[
                    "timestamp_ms"
                ],
            )
        )

        return {
            "positive_moment_count":
                len(
                    positive_moments
                ),

            "positive_moments":
                positive_moments,
        }