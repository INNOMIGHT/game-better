class PriorityAnalyzer:

    TASKS = {
        "fight_while_gold_behind": {
            "title":
                "Stop forcing fights when your team is already behind",

            "next_game_task":
                (
                    "Before committing to a fight, "
                    "check the team gold state indirectly "
                    "through items, completed components, "
                    "levels and recent objective losses. "
                    "If your team is clearly weaker, "
                    "look for farming, vision, picks or "
                    "numbers advantages instead of a "
                    "straight fight."
                ),
        },

        "fight_while_level_behind": {
            "title":
                "Check level advantages before fighting",

            "next_game_task":
                (
                    "Before an important fight, compare "
                    "your level and your nearby teammates' "
                    "levels against the opponents. Avoid "
                    "forcing even-number fights when your "
                    "team is multiple combined levels behind."
                ),
        },

        "outnumbered_fights": {
            "title":
                "Reduce outnumbered fight attempts",

            "next_game_task":
                (
                    "Before committing, count visible allies "
                    "and enemies. If you do not know where "
                    "multiple enemies are, assume the fight "
                    "may become unfavorable and preserve "
                    "your escape route."
                ),
        },

        "death_before_objective": {
            "title":
                "Prioritize staying alive before objectives",

            "next_game_task":
                (
                    "During the 60–90 seconds before Dragon "
                    "or Baron, reduce unnecessary side fights "
                    "and risky wave collection. Arrive alive, "
                    "with resources and position available "
                    "for the objective setup."
                ),
        },

        "high_impact_deaths": {
            "title":
                "Reduce deaths that create large tempo losses",

            "next_game_task":
                (
                    "When dying would expose towers, objectives "
                    "or large waves, value survival more highly. "
                    "Ask whether the potential reward is worth "
                    "losing map pressure for the next 30–60 seconds."
                ),
        },

        "level_gap_widening": {
            "title":
                "Avoid repeated fights while falling behind",

            "next_game_task":
                (
                    "After a losing fight, avoid immediately "
                    "taking another low-percentage fight. "
                    "Recover experience and resources first "
                    "unless the next fight is forced by a "
                    "major objective."
                ),
        },

        "farm_disruption": {
            "title":
                "Make your farming more resilient",

            "next_game_task":
                (
                    "When your normal farming pattern is interrupted, "
                    "identify the safest nearby wave or jungle resource "
                    "instead of allowing several low-resource minutes "
                    "to accumulate."
                ),
        },

        "farm_recovery_failure": {
            "title":
                "Recover your economy faster after disruptions",

            "next_game_task":
                (
                    "After a death, roam, recall or objective fight, "
                    "actively plan your next resource cycle. Avoid "
                    "drifting between plays without collecting waves "
                    "or camps unless your team immediately needs you."
                ),
        },

        "economic_disruption": {
            "title":
                "Reduce major economic slowdowns",

            "next_game_task":
                (
                    "Watch for periods where both gold and experience "
                    "generation fall sharply. After a play ends, choose "
                    "your next source of gold and XP quickly instead of "
                    "remaining in low-value map states."
                ),
        },

        "economic_recovery_failure": {
            "title":
                "Stabilize after losing economic momentum",

            "next_game_task":
                (
                    "When you fall behind economically, prioritize safe "
                    "resources and avoid repeated low-probability fights. "
                    "The goal is to restore gold and experience income "
                    "before taking another expensive risk."
                ),
        },


    }

    def build_priorities(
        self,
        weakness_analysis,
        max_priorities=5,
    ):

        weaknesses = (
            weakness_analysis.get(
                "weaknesses",
                [],
            )
        )

        priorities = []

        for weakness in weaknesses:
            task = self.TASKS.get(
                weakness["key"]
            )

            if (
                task is None
                and weakness[
                    "key"
                ].startswith(
                    "repeated_deaths_"
                )
            ):

                phase = (
                    weakness[
                        "key"
                    ]
                    .replace(
                        "repeated_deaths_",
                        "",
                    )
                )

                task = {
                    "title":
                        f"Reduce repeated deaths during the {phase} game",

                    "next_game_task":
                        (
                            f"During the {phase} game, treat each death "
                            "as a reset point. Before re-entering combat, "
                            "check whether your item, level, numbers and "
                            "objective situation have actually improved."
                        ),
                }

            confidence = (
                weakness.get(
                    "confidence",
                    "LOW",
                )
            )

            # Don't fill the player's
            # top priorities with weak
            # one-off evidence unless
            # we don't have anything else.
            if (
                confidence == "LOW"
                and
                len(priorities) >= 3
            ):
                continue

            priorities.append({
                "rank":
                    0,

                "weakness_key":
                    weakness[
                        "key"
                    ],

                "title":
                    task[
                        "title"
                    ],

                "score":
                    weakness[
                        "score"
                    ],

                "confidence":
                    confidence,

                "evidence": {
                    "occurrences":
                        weakness[
                            "occurrences"
                        ],

                    "matches_affected":
                        weakness[
                            "matches_affected"
                        ],

                    "matches_analyzed":
                        weakness[
                            "matches_analyzed"
                        ],

                    "average_severity":
                        weakness[
                            "average_severity"
                        ],

                    "high_impact_occurrences":
                        weakness[
                            "high_impact_occurrences"
                        ],

                    "average_minute":
                        weakness[
                            "average_minute"
                        ],
                },

                "next_game_task":
                    task[
                        "next_game_task"
                    ],
            })

            if (
                len(priorities)
                >= max_priorities
            ):
                break

        for index, priority in enumerate(
            priorities,
            start=1,
        ):

            priority[
                "rank"
            ] = index

        return {
            "priority_count":
                len(
                    priorities
                ),

            "priorities":
                priorities,
        }