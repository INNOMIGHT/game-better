class CoachingSignalAdapter:
    """
    Converts detector/analyzer outputs into one common format.

    The WeaknessAnalyzer should not need to understand
    the raw output structure of every detector.
    """

    # --------------------------------------------------
    # Generic builder
    # --------------------------------------------------

    @staticmethod
    def _signal(
        *,
        key,
        category,
        title,
        severity,
        minute=None,
        evidence=None,
        source=None,
        positive=False,
    ):
        return {
            "key": key,
            "category": category,
            "title": title,

            # Expected range 1 -> 5
            "severity": max(
                1,
                min(
                    int(round(severity)),
                    5,
                ),
            ),

            "minute": minute,

            "evidence": (
                evidence
                or {}
            ),

            "source": source,

            "positive": positive,
        }

    # ==================================================
    # FARMING
    # ==================================================

    def from_farming_disruptions(
        self,
        disruptions,
    ):
        """
        Expected disruption dictionaries may contain things like:

        minute
        relative_drop
        baseline_cs_per_min
        observed_cs_per_min
        recovered
        recovery_minutes
        events

        Missing keys are handled safely.
        """

        signals = []

        for disruption in (
            disruptions
            or []
        ):

            relative_drop = (
                disruption.get(
                    "relative_drop"
                )
                or disruption.get(
                    "relative_cs_drop"
                )
                or 0
            )

            minute = (
                disruption.get(
                    "minute"
                )
                or disruption.get(
                    "start_minute"
                )
                or disruption.get(
                    "disruption_minute"
                )
            )

            recovered = (
                disruption.get(
                    "recovered"
                )
            )

            # ------------------------------------------
            # Severity from size of farming collapse
            # ------------------------------------------

            if relative_drop >= 0.70:
                severity = 5

            elif relative_drop >= 0.50:
                severity = 4

            elif relative_drop >= 0.30:
                severity = 3

            else:
                severity = 2

            signals.append(
                self._signal(
                    key=
                        "farm_disruption",

                    category=
                        "FARMING",

                    title=
                        "Farming rate collapsed",

                    severity=
                        severity,

                    minute=
                        minute,

                    source=
                        "FarmingDisruptionDetector",

                    evidence={
                        "relative_drop":
                            relative_drop,

                        "baseline_cs_per_min":
                            disruption.get(
                                "baseline_cs_per_min"
                            ),

                        "observed_cs_per_min":
                            disruption.get(
                                "observed_cs_per_min"
                            ),
                    },
                )
            )

            # ------------------------------------------
            # Failed recovery
            # ------------------------------------------

            if recovered is False:

                signals.append(
                    self._signal(
                        key=
                            "farm_recovery_failure",

                        category=
                            "FARMING",

                        title=
                            "Failed to recover farming after disruption",

                        severity=
                            min(
                                severity + 1,
                                5,
                            ),

                        minute=
                            minute,

                        source=
                            "FarmingDisruptionDetector",

                        evidence={
                            "relative_drop":
                                relative_drop,

                            "recovered":
                                False,
                        },
                    )
                )

            elif recovered is True:

                signals.append(
                    self._signal(
                        key=
                            "farm_recovery_success",

                        category=
                            "FARMING",

                        title=
                            "Recovered farming after disruption",

                        severity=
                            severity,

                        minute=
                            minute,

                        source=
                            "FarmingDisruptionDetector",

                        positive=True,

                        evidence={
                            "relative_drop":
                                relative_drop,

                            "recovered":
                                True,
                        },
                    )
                )

        return signals

    # ==================================================
    # ECONOMY
    # ==================================================

    def from_economic_disruptions(
        self,
        disruptions,
    ):

        signals = []

        for disruption in (
            disruptions
            or []
        ):

            minute = (
                disruption.get(
                    "minute"
                )
                or disruption.get(
                    "start_minute"
                )
                or disruption.get(
                    "disruption_minute"
                )
            )

            gold_drop = (
                disruption.get(
                    "gold_relative_drop"
                )
                or disruption.get(
                    "relative_gold_drop"
                )
                or 0
            )

            xp_drop = (
                disruption.get(
                    "xp_relative_drop"
                )
                or disruption.get(
                    "relative_xp_drop"
                )
                or 0
            )

            largest_drop = max(
                gold_drop,
                xp_drop,
            )

            if largest_drop >= 0.60:
                severity = 5

            elif largest_drop >= 0.40:
                severity = 4

            elif largest_drop >= 0.25:
                severity = 3

            else:
                severity = 2

            signals.append(
                self._signal(
                    key=
                        "economic_disruption",

                    category=
                        "ECONOMY",

                    title=
                        "Economic momentum collapsed",

                    severity=
                        severity,

                    minute=
                        minute,

                    source=
                        "EconomicDisruptionDetector",

                    evidence={
                        "gold_relative_drop":
                            gold_drop,

                        "xp_relative_drop":
                            xp_drop,
                    },
                )
            )

            recovered = (
                disruption.get(
                    "recovered"
                )
            )

            if recovered is False:

                signals.append(
                    self._signal(
                        key=
                            "economic_recovery_failure",

                        category=
                            "ECONOMY",

                        title=
                            "Failed to recover economic momentum",

                        severity=
                            min(
                                severity + 1,
                                5,
                            ),

                        minute=
                            minute,

                        source=
                            "EconomicDisruptionDetector",

                        evidence={
                            "recovered":
                                False,

                            "gold_relative_drop":
                                gold_drop,

                            "xp_relative_drop":
                                xp_drop,
                        },
                    )
                )

        return signals

    # ==================================================
    # DEATH PATTERNS
    # ==================================================

    def from_death_patterns(
        self,
        death_analysis,
    ):
        """
        Converts higher-level death-pattern output.

        This is intentionally defensive because your
        detector may expose phase counts/rates slightly
        differently.
        """

        signals = []

        if not death_analysis:
            return signals

        phases = (
            death_analysis.get(
                "phases"
            )
            or death_analysis.get(
                "phase_stats"
            )
            or {}
        )

        for phase_name, phase in (
            phases.items()
        ):

            deaths = (
                phase.get(
                    "deaths"
                )
                or phase.get(
                    "death_count"
                )
                or 0
            )

            if deaths < 2:
                continue

            if deaths >= 4:
                severity = 5

            elif deaths == 3:
                severity = 4

            else:
                severity = 3

            signals.append(
                self._signal(
                    key=
                        f"repeated_deaths_{phase_name}",

                    category=
                        "DEATHS",

                    title=
                        f"Repeated deaths during {phase_name} game",

                    severity=
                        severity,

                    source=
                        "DeathPatternDetector",

                    evidence={
                        "phase":
                            phase_name,

                        "deaths":
                            deaths,
                    },
                )
            )

        return signals

    # ==================================================
    # CRITICAL MOMENTS
    # ==================================================

    def from_critical_moments(
        self,
        moments,
    ):

        signals = []

        reason_map = {
            "team_gold_disadvantage": (
                "fight_while_gold_behind",
                "FIGHT_SELECTION",
                "Fought while team was behind in gold",
            ),

            "team_level_disadvantage": (
                "fight_while_level_behind",
                "FIGHT_SELECTION",
                "Fought while team was behind in levels",
            ),

            "local_number_disadvantage": (
                "outnumbered_fight",
                "FIGHT_SELECTION",
                "Took a locally outnumbered fight",
            ),

            "enemy_objective_after_death": (
                "death_before_objective",
                "OBJECTIVES",
                "Death preceded an enemy major objective",
            ),

            "gap_widened_after_death": (
                "high_impact_death",
                "DEATHS",
                "Death was followed by a larger economic deficit",
            ),
        }

        for moment in (
            moments
            or []
        ):

            severity = (
                moment.get(
                    "severity",
                    1,
                )
            )

            for reason in (
                moment.get(
                    "reasons",
                    []
                )
            ):

                mapping = (
                    reason_map.get(
                        reason
                    )
                )

                if mapping is None:
                    continue

                (
                    key,
                    category,
                    title,
                ) = mapping

                signals.append(
                    self._signal(
                        key=
                            key,

                        category=
                            category,

                        title=
                            title,

                        severity=
                            severity,

                        minute=
                            moment.get(
                                "minute"
                            ),

                        source=
                            "CriticalMomentAnalyzer",

                        evidence={
                            "team_gold_difference":
                                moment.get(
                                    "before",
                                    {},
                                ).get(
                                    "team_gold_difference"
                                ),

                            "team_level_difference":
                                moment.get(
                                    "before",
                                    {},
                                ).get(
                                    "team_level_difference"
                                ),

                            "gold_difference_change":
                                moment.get(
                                    "change",
                                    {},
                                ).get(
                                    "gold_difference_change"
                                ),
                        },
                    )
                )

        return signals

    # ==================================================
    # POSITIVE MOMENTS
    # ==================================================

    def from_positive_moments(
        self,
        moments,
    ):

        signals = []

        for moment in (
            moments
            or []
        ):

            reasons = set(
                moment.get(
                    "reasons",
                    []
                )
            )

            if (
                "objective_conversion"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "successful_objective_conversion",

                        category=
                            "OBJECTIVES",

                        title=
                            "Converted combat success into an objective",

                        severity=
                            moment.get(
                                "impact_score",
                                3,
                            ),

                        minute=
                            moment.get(
                                "minute"
                            ),

                        source=
                            "PositiveMomentAnalyzer",

                        positive=True,

                        evidence={
                            "objective":
                                moment.get(
                                    "objective_conversion"
                                )
                        },
                    )
                )

        return signals