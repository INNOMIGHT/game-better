class RecommendationEngine:

    def _death_recommendation(
        self,
        moment,
    ):

        reasons = set(
            moment.get(
                "reasons",
                [],
            )
        )

        before = moment[
            "before"
        ]

        after = moment[
            "after_90_seconds"
        ]

        minute = moment[
            "minute"
        ]

        recommendations = []

        # ----------------------------------
        # Fighting while team is behind
        # ----------------------------------

        if (
            "team_level_disadvantage"
            in reasons
            and
            "team_gold_disadvantage"
            in reasons
        ):

            recommendations.append({
                "category":
                    "FIGHT_SELECTION",

                "priority":
                    "HIGH",

                "minute":
                    minute,

                "title":
                    "Avoid forcing fights "
                    "from a clear team disadvantage",

                "evidence": {
                    "gold_difference":
                        before[
                            "team_gold_difference"
                        ],

                    "level_difference":
                        before[
                            "team_level_difference"
                        ],
                },

                "recommendation":
                    (
                        "Your team was already "
                        "behind in both gold and "
                        "levels when you died. "
                        "Unless your team has "
                        "another strong advantage "
                        "such as numbers, vision, "
                        "positioning, or cooldowns, "
                        "look for safer resource "
                        "collection or a more "
                        "favorable fight."
                    ),
            })

        # ----------------------------------
        # Death followed by larger deficit
        # ----------------------------------

        if (
            "gap_widened_after_death"
            in reasons
        ):

            before_gold = (
                before[
                    "team_gold_difference"
                ]
            )

            after_gold = (
                after[
                    "team_gold_difference"
                ]
            )

            recommendations.append({
                "category":
                    "DEATH_IMPACT",

                "priority":
                    "HIGH",

                "minute":
                    minute,

                "title":
                    "This death was followed "
                    "by a major loss of tempo",

                "evidence": {
                    "gold_difference_before":
                        before_gold,

                    "gold_difference_after":
                        after_gold,

                    "difference_change":
                        (
                            after_gold
                            - before_gold
                        ),
                },

                "recommendation":
                    (
                        "The team's gold position "
                        "became significantly worse "
                        "during the 90 seconds after "
                        "this death. Review whether "
                        "the fight was necessary and "
                        "whether disengaging would "
                        "have preserved map pressure "
                        "and resources."
                    ),
            })
        # ----------------------------------
        # Local number disadvantage
        # ----------------------------------

        if (
            "local_number_disadvantage"
            in reasons
        ):

            local = (
                moment.get(
                    "local_fight_context"
                )
                or {}
            )

            recommendations.append({
                "category":
                    "FIGHT_SELECTION",

                "priority":
                    "HIGH",

                "minute":
                    minute,

                "title":
                    "Avoid taking locally "
                    "outnumbered fights",

                "evidence": {
                    "nearby_allies":
                        local.get(
                            "nearby_allies"
                        ),

                    "nearby_enemies":
                        local.get(
                            "nearby_enemies"
                        ),

                    "number_difference":
                        local.get(
                            "number_difference"
                        ),

                    "position_estimate":
                        True,
                },

                "recommendation":
                    (
                        "The latest available "
                        "position data suggests "
                        "you were locally "
                        "outnumbered when this "
                        "death occurred. Unless "
                        "you have a strong "
                        "compensating advantage, "
                        "wait for teammates or "
                        "disengage rather than "
                        "committing to the fight."
                    ),
            })

        return recommendations

    def build_match_recommendations(
        self,
        critical_moments,
    ):

        recommendations = []

        for moment in critical_moments:

            if (
                moment["type"]
                == "PLAYER_DEATH"
            ):

                recommendations.extend(
                    self._death_recommendation(
                        moment
                    )
                )

        # ----------------------------------
        # Sort important advice first
        # ----------------------------------

        priority_order = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        recommendations.sort(
            key=lambda item:
                priority_order.get(
                    item["priority"],
                    0,
                ),
            reverse=True,
        )

        return recommendations