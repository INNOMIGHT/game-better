class PriorityAnalyzer:

    MAX_PRIORITIES = 5

    TASKS = {
        # ==========================================
        # FIGHT SELECTION
        # ==========================================

        "fight_while_gold_behind": {
            "title":
                "Improve fight selection when behind",

            "category":
                "FIGHT_SELECTION",

            "action":
                (
                    "Avoid forcing fights when your team "
                    "is already behind in gold. Look for "
                    "safer farm, vision, picks, or a better "
                    "numbers advantage first."
                ),
        },

        "fight_while_level_behind": {
            "title":
                "Respect level disadvantages",

            "category":
                "FIGHT_SELECTION",

            "action":
                (
                    "Before committing to a fight, check "
                    "important level and ultimate advantages. "
                    "Avoid equal-number fights when your team "
                    "is materially behind in levels."
                ),
        },

        # STANDARDIZED SINGULAR KEY
        "outnumbered_fight": {
            "title":
                "Reduce outnumbered fights",

            "category":
                "FIGHT_SELECTION",

            "action":
                (
                    "Avoid committing when nearby enemy "
                    "numbers exceed your team's available "
                    "numbers. Wait for teammates or disengage."
                ),
        },

        # ==========================================
        # OBJECTIVES / SURVIVAL
        # ==========================================

        "death_before_objective": {
            "title":
                "Stay alive before major objectives",

            "category":
                "OBJECTIVES",

            "action":
                (
                    "Prioritize survival before Dragon, "
                    "Baron, or Herald windows. Avoid low-value "
                    "fights when your death could leave your "
                    "team unable to contest."
                ),
        },

        # STANDARDIZED SINGULAR KEY
        "high_impact_death": {
            "title":
                "Reduce high-impact deaths",

            "category":
                "SURVIVAL",

            "action":
                (
                    "Identify deaths that are followed by "
                    "large economic swings and play those "
                    "situations more conservatively."
                ),
        },

        "level_gap_widening": {
            "title":
                "Avoid deaths while already behind",

            "category":
                "SURVIVAL",

            "action":
                (
                    "When your team is behind in levels, "
                    "avoid deaths that allow the opponent "
                    "to extend the level advantage further."
                ),
        },

        # ==========================================
        # FARMING
        # ==========================================

        "farm_disruption": {
            "title":
                "Reduce farming disruptions",

            "category":
                "FARMING",

            "action":
                (
                    "Look for the events that repeatedly "
                    "interrupt your farming tempo and avoid "
                    "unnecessary downtime between waves "
                    "and objectives."
                ),
        },

        "farm_recovery_failure": {
            "title":
                "Improve recovery after losing farm tempo",

            "category":
                "FARMING",

            "action":
                (
                    "After a death, roam, or disrupted lane, "
                    "prioritize a safe route back into reliable "
                    "farm instead of immediately forcing another "
                    "low-probability play."
                ),
        },

        # ==========================================
        # ECONOMY
        # ==========================================

        "economic_disruption": {
            "title":
                "Protect your economy",

            "category":
                "ECONOMY",

            "action":
                (
                    "Reduce periods where your gold or "
                    "experience generation falls sharply "
                    "relative to your earlier pace."
                ),
        },

        "economic_recovery_failure": {
            "title":
                "Recover economy more efficiently",

            "category":
                "ECONOMY",

            "action":
                (
                    "After falling behind economically, "
                    "focus on high-certainty resources and "
                    "safe experience before taking another "
                    "high-risk fight."
                ),
        },

        # ==========================================
        # RANK-RELATIVE PERFORMANCE
        # ==========================================

        "early_farming": {
            "title":
                "Improve early farming consistency",

            "category":
                "FARMING",

            "action":
                (
                    "Your early farming is below the supported "
                    "baseline for progression in your role. "
                    "Prioritize wave collection and reduce "
                    "unnecessary early CS losses."
                ),
        },

        "sustained_farming": {
            "title":
                "Maintain farm through mid game",

            "category":
                "FARMING",

            "action":
                (
                    "Your early game may be acceptable, but "
                    "your sustained farm is below the supported "
                    "next-rank baseline. Improve side-wave and "
                    "safe resource collection between fights."
                ),
        },

        "early_economy": {
            "title":
                "Improve early gold generation",

            "category":
                "ECONOMY",

            "action":
                (
                    "Your early gold generation is below a "
                    "supported role-and-rank baseline. Focus on "
                    "reliable lane resources and higher-value "
                    "early decisions."
                ),
        },

        "sustained_economy": {
            "title":
                "Improve sustained gold generation",

            "category":
                "ECONOMY",

            "action":
                (
                    "Your gold generation falls below supported "
                    "higher-rank role baselines over the full "
                    "game. Reduce resource downtime between "
                    "major events."
                ),
        },

        "early_experience": {
            "title":
                "Improve early experience efficiency",

            "category":
                "ECONOMY",

            "action":
                (
                    "Avoid unnecessary early experience losses. "
                    "Protect wave experience and reduce time "
                    "spent away from productive map activity."
                ),
        },

        "survival_efficiency": {
            "title":
                "Improve survival efficiency",

            "category":
                "SURVIVAL",

            "action":
                (
                    "Your death profile is below the relevant "
                    "role baseline. Focus on avoiding low-value "
                    "deaths rather than simply playing more "
                    "passively."
                ),
        },

        "combat_efficiency": {
            "title":
                "Improve combat efficiency",

            "category":
                "COMBAT",

            "action":
                (
                    "Improve the value you generate from fights "
                    "relative to the risks you take."
                ),
        },
    }

    # ==================================================
    # TASK RESOLUTION
    # ==================================================

    def _task_for_weakness(
        self,
        weakness,
    ):

        key = (
            weakness.get(
                "key"
            )
        )

        # Dynamic death-phase signals.
        if (
            key
            and
            key.startswith(
                "repeated_deaths_"
            )
        ):

            phase = (
                key.replace(
                    "repeated_deaths_",
                    ""
                )
            )

            return {
                "title":
                    (
                        f"Reduce repeated "
                        f"{phase}-game deaths"
                    ),

                "category":
                    "SURVIVAL",

                "action":
                    (
                        f"Review recurring deaths during the "
                        f"{phase} phase and identify whether "
                        "they come from positioning, numbers "
                        "disadvantages, or unnecessary fights."
                    ),
            }

        return (
            self.TASKS.get(
                key
            )
        )

    # ==================================================
    # PRIORITY SCORE
    # ==================================================

    @staticmethod
    def _priority_score(
        weakness,
    ):

        weakness_score = float(
            weakness.get(
                "weakness_score",
                0,
            )
            or 0
        )

        severity_total = float(
            weakness.get(
                "severity_total",
                0,
            )
            or 0
        )

        occurrences = float(
            weakness.get(
                "occurrences",
                0,
            )
            or 0
        )

        high_impact = float(
            weakness.get(
                "high_impact_occurrences",
                0,
            )
            or 0
        )

        # Weakness score remains the dominant term.
        #
        # Extra recurrence/impact helps break ties.
        score = (
            weakness_score
            +
            min(
                severity_total / 50.0,
                0.15,
            )
            +
            min(
                occurrences / 50.0,
                0.10,
            )
            +
            min(
                high_impact / 20.0,
                0.10,
            )
        )

        return round(
            score,
            4,
        )

    # ==================================================
    # ANALYZE
    # ==================================================

    def analyze(
        self,
        weaknesses,
        max_priorities=None,
    ):

        if max_priorities is None:

            max_priorities = (
                self.MAX_PRIORITIES
            )

        candidates = []

        for weakness in (
            weaknesses or []
        ):

            task = (
                self._task_for_weakness(
                    weakness
                )
            )

            if task is None:
                continue

            confidence = (
                weakness.get(
                    "confidence",
                    "LOW",
                )
            )

            candidate = {
                "key":
                    weakness.get(
                        "key"
                    ),

                "title":
                    task[
                        "title"
                    ],

                "category":
                    task[
                        "category"
                    ],

                "action":
                    task[
                        "action"
                    ],

                "priority_score":
                    self._priority_score(
                        weakness
                    ),

                "weakness_score":
                    weakness.get(
                        "weakness_score"
                    ),

                "confidence":
                    confidence,

                "occurrences":
                    weakness.get(
                        "occurrences",
                        0,
                    ),

                "matches":
                    weakness.get(
                        "match_count",
                        weakness.get(
                            "matches_analyzed",
                            0,
                        ),
                    ),

                "high_impact_occurrences":
                    weakness.get(
                        "high_impact_occurrences",
                        0,
                    ),

                "examples":
                    weakness.get(
                        "examples",
                        [],
                    ),
            }

            candidates.append(
                candidate
            )

        # ------------------------------------------
        # Highest-value problems first.
        # ------------------------------------------

        candidates.sort(
            key=lambda item:
                item[
                    "priority_score"
                ],
            reverse=True,
        )

        # ==========================================
        # CONFIDENCE-AWARE SELECTION
        #
        # Prefer HIGH/MEDIUM evidence.
        # Allow LOW evidence only when we still
        # need priorities.
        # ==========================================

        strong = [
            item
            for item in candidates
            if (
                item[
                    "confidence"
                ]
                in {
                    "HIGH",
                    "MEDIUM",
                }
            )
        ]

        low = [
            item
            for item in candidates
            if (
                item[
                    "confidence"
                ]
                not in {
                    "HIGH",
                    "MEDIUM",
                }
            )
        ]

        selected = []

        # Prefer at least the strongest supported
        # priorities first.

        for item in strong:

            if (
                len(selected)
                >= max_priorities
            ):
                break

            selected.append(
                item
            )

        # Fill remaining slots if necessary.

        for item in low:

            if (
                len(selected)
                >= max_priorities
            ):
                break

            selected.append(
                item
            )

        return selected