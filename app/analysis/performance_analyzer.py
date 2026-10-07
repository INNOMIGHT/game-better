class PerformanceAnalyzer:

    PHASES = {
        "early": (
            0,
            14,
        ),

        "mid": (
            14,
            25,
        ),

        "late": (
            25,
            float("inf"),
        ),
    }

    @staticmethod
    def _total_cs(frame):

        return (
            (frame.minions_killed or 0)
            + (
                frame.jungle_minions_killed
                or 0
            )
        )

    def _frames_in_phase(
        self,
        frames,
        start_minute,
        end_minute,
    ):

        return [
            frame
            for frame in frames
            if (
                frame.timestamp_ms
                / 60_000
                >= start_minute
                and
                frame.timestamp_ms
                / 60_000
                < end_minute
            )
        ]

    def _phase_summary(
        self,
        frames,
        start_minute,
        end_minute,
    ):

        phase_frames = (
            self._frames_in_phase(
                frames,
                start_minute,
                end_minute,
            )
        )

        if len(
            phase_frames
        ) < 2:

            return None

        first = phase_frames[0]

        last = phase_frames[-1]

        elapsed_minutes = (
            (
                last.timestamp_ms
                - first.timestamp_ms
            )
            / 60_000
        )

        if elapsed_minutes <= 0:
            return None

        cs_gain = (
            self._total_cs(last)
            - self._total_cs(first)
        )

        gold_gain = (
            (last.total_gold or 0)
            - (first.total_gold or 0)
        )

        xp_gain = (
            (last.xp or 0)
            - (first.xp or 0)
        )

        return {
            "start_minute":
                round(
                    first.timestamp_ms
                    / 60_000,
                    2,
                ),

            "end_minute":
                round(
                    last.timestamp_ms
                    / 60_000,
                    2,
                ),

            "cs_per_minute":
                round(
                    cs_gain
                    / elapsed_minutes,
                    2,
                ),

            "gold_per_minute":
                round(
                    gold_gain
                    / elapsed_minutes,
                    2,
                ),

            "xp_per_minute":
                round(
                    xp_gain
                    / elapsed_minutes,
                    2,
                ),

            "level_start":
                first.level,

            "level_end":
                last.level,
        }

    def analyze(
        self,
        player,
        player_frames,
        events,
    ):

        player_frames = sorted(
            player_frames,
            key=lambda frame:
                frame.timestamp_ms,
        )

        phase_results = {}

        for phase, (
            start,
            end,
        ) in self.PHASES.items():

            phase_results[phase] = (
                self._phase_summary(
                    frames=
                        player_frames,
                    start_minute=start,
                    end_minute=end,
                )
            )

        deaths = 0
        kills = 0
        assists = 0

        for event in events:

            if (
                event.event_type
                != "CHAMPION_KILL"
            ):
                continue

            if (
                event.victim_id
                == player.participant_id
            ):
                deaths += 1

            if (
                event.killer_id
                == player.participant_id
            ):
                kills += 1

            raw = (
                event.raw_data
                or {}
            )

            assisting_ids = (
                raw.get(
                    "assistingParticipantIds",
                    [],
                )
            )

            if (
                player.participant_id
                in assisting_ids
            ):
                assists += 1

        return {
            "champion":
                player.champion_name,

            "role":
                player.role,

            "win":
                bool(
                    player.win
                ),

            "kills":
                kills,

            "deaths":
                deaths,

            "assists":
                assists,

            "phases":
                phase_results,
        }