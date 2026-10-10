class CoachingSignalAdapter:

    # ==================================================
    # SIGNAL FACTORY
    # ==================================================

    @staticmethod
    def _signal(
        *,
        key,
        category,
        title,
        severity,
        source,
        positive=False,
        minute=None,
        evidence=None,
    ):

        severity = max(
            1,
            min(
                int(severity),
                5,
            ),
        )

        return {
            "key":
                key,

            "category":
                category,

            "title":
                title,

            "severity":
                severity,

            "minute":
                minute,

            "evidence":
                evidence or {},

            "source":
                source,

            "positive":
                bool(
                    positive
                ),
        }

    # ==================================================
    # COMMON HELPERS
    # ==================================================

    @staticmethod
    def _confidence_severity(
        confidence,
        default=3,
    ):

        if not confidence:
            return default

        confidence = str(
            confidence
        ).upper()

        return {
            "VERY_LOW": 2,
            "LOW": 2,
            "MEDIUM": 3,
            "HIGH": 4,
            "VERY_HIGH": 5,
        }.get(
            confidence,
            default,
        )

    @staticmethod
    def _first_number(
        data,
        *keys,
    ):

        for key in keys:

            value = data.get(
                key
            )

            if value is not None:
                return value

        return None

    # ==================================================
    # FARMING
    # ==================================================

    def from_farming_disruptions(
        self,
        disruptions,
    ):

        signals = []

        for disruption in (
            disruptions or []
        ):

            if not isinstance(
                disruption,
                dict,
            ):
                continue

            minute = (
                self._first_number(
                    disruption,
                    "minute",
                    "disruption_minute",
                    "start_minute",
                )
            )

            confidence = (
                disruption.get(
                    "confidence"
                )
            )

            percentage_drop = (
                disruption.get(
                    "percentage_drop"
                )
            )

            severity = (
                self._confidence_severity(
                    confidence,
                    default=3,
                )
            )

            # Large observed drops can increase the
            # evidence significance slightly.
            if percentage_drop is not None:

                try:

                    percentage_drop = float(
                        percentage_drop
                    )

                    if percentage_drop >= 70:
                        severity = max(
                            severity,
                            4,
                        )

                    elif percentage_drop >= 50:
                        severity = max(
                            severity,
                            3,
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            signals.append(
                self._signal(
                    key=
                        "farm_disruption",

                    category=
                        "FARMING",

                    title=
                        "Farming rate dropped",

                    severity=
                        severity,

                    minute=
                        minute,

                    source=
                        "farming_disruption",

                    evidence=
                        disruption,
                )
            )

            # Actual FARM_002 payload:
            #
            # recovered_next_interval
            #
            # Preserve fallback support for
            # the previous generic "recovered" field.

            recovered = (
                disruption.get(
                    "recovered_next_interval"
                )
            )

            if recovered is None:

                recovered = (
                    disruption.get(
                        "recovered"
                    )
                )

            if recovered is True:

                signals.append(
                    self._signal(
                        key=
                            "farm_recovery_success",

                        category=
                            "FARMING",

                        title=
                            "Recovered farming tempo",

                        severity=
                            max(
                                severity,
                                2,
                            ),

                        minute=
                            minute,

                        source=
                            "farming_disruption",

                        positive=
                            True,

                        evidence=
                            disruption,
                    )
                )

            elif recovered is False:

                signals.append(
                    self._signal(
                        key=
                            "farm_recovery_failure",

                        category=
                            "FARMING",

                        title=
                            "Farming tempo did not recover immediately",

                        severity=
                            max(
                                severity,
                                3,
                            ),

                        minute=
                            minute,

                        source=
                            "farming_disruption",

                        evidence=
                            disruption,
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
            disruptions or []
        ):

            if not isinstance(
                disruption,
                dict,
            ):
                continue

            minute = (
                self._first_number(
                    disruption,
                    "minute",
                    "disruption_minute",
                    "start_minute",
                )
            )

            severity = (
                disruption.get(
                    "severity"
                )
            )

            if severity is None:

                severity = (
                    self._confidence_severity(
                        disruption.get(
                            "confidence"
                        ),
                        default=3,
                    )
                )

            metric = (
                disruption.get(
                    "metric"
                )
                or disruption.get(
                    "metric_name"
                )
            )

            if metric:

                title = (
                    f"{str(metric).upper()} "
                    f"generation disruption"
                )

            else:

                title = (
                    "Economic disruption"
                )

            signals.append(
                self._signal(
                    key=
                        "economic_disruption",

                    category=
                        "ECONOMY",

                    title=
                        title,

                    severity=
                        severity,

                    minute=
                        minute,

                    source=
                        "economic_disruption",

                    evidence=
                        disruption,
                )
            )

            # Support either current or future
            # recovery field names.

            recovered = (
                disruption.get(
                    "recovered_next_interval"
                )
            )

            if recovered is None:

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
                            "Economic generation did not recover immediately",

                        severity=
                            max(
                                int(
                                    severity
                                ),
                                3,
                            ),

                        minute=
                            minute,

                        source=
                            "economic_disruption",

                        evidence=
                            disruption,
                    )
                )

            elif recovered is True:

                signals.append(
                    self._signal(
                        key=
                            "economic_recovery_success",

                        category=
                            "ECONOMY",

                        title=
                            "Recovered economic tempo",

                        severity=
                            max(
                                int(
                                    severity
                                ),
                                2,
                            ),

                        minute=
                            minute,

                        source=
                            "economic_disruption",

                        positive=
                            True,

                        evidence=
                            disruption,
                    )
                )

        return signals

    # ==================================================
    # DEATH PATTERNS
    # ==================================================

    def from_death_patterns(
        self,
        death_patterns,
    ):

        signals = []

        if not death_patterns:
            return signals

        # ==========================================
        # NORMALIZE DEATH_001 PAYLOAD
        #
        # Actual structure:
        #
        # {
        #     "detector_id": "DEATH_001",
        #     "matches_analyzed": 1,
        #     "match_results": [
        #         {
        #             "phases": ...
        #         }
        #     ],
        #     ...
        # }
        #
        # Also preserve support for older/direct
        # phase structures.
        # ==========================================

        phase_sets = []

        if isinstance(
            death_patterns,
            dict,
        ):

            match_results = (
                death_patterns.get(
                    "match_results"
                )
            )

            if isinstance(
                match_results,
                list,
            ):

                for match_result in (
                    match_results
                ):

                    if not isinstance(
                        match_result,
                        dict,
                    ):
                        continue

                    phases = (
                        match_result.get(
                            "phases"
                        )
                    )

                    if isinstance(
                        phases,
                        dict,
                    ):

                        phase_sets.append(
                            {
                                "phases":
                                    phases,

                                "match_result":
                                    match_result,
                            }
                        )

            else:

                phases = (
                    death_patterns.get(
                        "phases"
                    )
                )

                if isinstance(
                    phases,
                    dict,
                ):

                    phase_sets.append(
                        {
                            "phases":
                                phases,

                            "match_result":
                                death_patterns,
                        }
                    )

                else:

                    phase_sets.append(
                        {
                            "phases":
                                death_patterns,

                            "match_result":
                                death_patterns,
                        }
                    )

        # ==========================================
        # BUILD PHASE SIGNALS
        # ==========================================

        for phase_set in phase_sets:

            phases = (
                phase_set[
                    "phases"
                ]
            )

            match_result = (
                phase_set[
                    "match_result"
                ]
            )

            for phase in (
                "early",
                "mid",
                "late",
            ):

                data = (
                    phases.get(
                        phase
                    )
                )

                if not isinstance(
                    data,
                    dict,
                ):
                    continue

                deaths = (
                    data.get(
                        "deaths"
                    )
                )

                if deaths is None:

                    deaths = (
                        data.get(
                            "death_count"
                        )
                    )

                if deaths is None:
                    deaths = 0

                repeated = (
                    data.get(
                        "repeated_deaths"
                    )
                )

                if repeated is None:

                    repeated = (
                        deaths >= 2
                    )

                if not repeated:
                    continue

                if deaths >= 4:

                    severity = 5

                elif deaths >= 3:

                    severity = 4

                else:

                    severity = 3

                evidence = {
                    "phase":
                        phase,

                    "phase_data":
                        data,

                    "total_match_deaths":
                        match_result.get(
                            "total_deaths"
                        ),

                    "detector_id":
                        death_patterns.get(
                            "detector_id"
                        ),
                }

                signals.append(
                    self._signal(
                        key=
                            f"repeated_deaths_{phase}",

                        category=
                            "SURVIVAL",

                        title=
                            (
                                f"Repeated "
                                f"{phase}-game deaths"
                            ),

                        severity=
                            severity,

                        source=
                            "death_patterns",

                        evidence=
                            evidence,
                    )
                )

        return signals

    # ==================================================
    # CRITICAL MOMENTS
    # ==================================================

    def from_critical_moments(
        self,
        critical_moments,
    ):

        signals = []

        for moment in (
            critical_moments or []
        ):

            if not isinstance(
                moment,
                dict,
            ):
                continue

            minute = (
                moment.get(
                    "minute"
                )
            )

            if (
                minute is None
                and
                moment.get(
                    "timestamp_ms"
                )
                is not None
            ):

                minute = round(
                    (
                        moment[
                            "timestamp_ms"
                        ]
                        / 60000
                    ),
                    2,
                )

            severity = (
                moment.get(
                    "severity"
                )
                or 3
            )

            # ==========================================
            # IMPORTANT:
            #
            # CriticalMomentAnalyzer stores findings in:
            #
            # moment["reasons"]
            #
            # NOT as top-level booleans.
            # ==========================================

            reasons = set(
                moment.get(
                    "reasons",
                    [],
                )
                or []
            )

            # ------------------------------------------
            # GOLD DISADVANTAGE
            # ------------------------------------------

            if (
                "team_gold_disadvantage"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "fight_while_gold_behind",

                        category=
                            "FIGHT_SELECTION",

                        title=
                            "Died while team was behind in gold",

                        severity=
                            severity,

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

            # ------------------------------------------
            # LEVEL DISADVANTAGE
            # ------------------------------------------

            if (
                "team_level_disadvantage"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "fight_while_level_behind",

                        category=
                            "FIGHT_SELECTION",

                        title=
                            "Died while team was behind in levels",

                        severity=
                            severity,

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

            # ------------------------------------------
            # LOCAL NUMBER DISADVANTAGE
            # ------------------------------------------

            if (
                "local_number_disadvantage"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "outnumbered_fight",

                        category=
                            "FIGHT_SELECTION",

                        title=
                            "Died while locally outnumbered",

                        severity=
                            severity,

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

            # ------------------------------------------
            # OBJECTIVE WINDOW
            # ------------------------------------------

            if (
                "enemy_objective_after_death"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "death_before_objective",

                        category=
                            "OBJECTIVES",

                        title=
                            "Death shortly before enemy objective",

                        severity=
                            max(
                                int(
                                    severity
                                ),
                                4,
                            ),

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

            # ------------------------------------------
            # GOLD DEFICIT WIDENED AFTER DEATH
            # ------------------------------------------

            if (
                "gap_widened_after_death"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "high_impact_death",

                        category=
                            "SURVIVAL",

                        title=
                            "Team gold position worsened after this death",

                        severity=
                            max(
                                int(
                                    severity
                                ),
                                4,
                            ),

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

            # ------------------------------------------
            # LEVEL DEFICIT WIDENED
            # ------------------------------------------

            if (
                "level_gap_widened"
                in reasons
            ):

                signals.append(
                    self._signal(
                        key=
                            "level_gap_widening",

                        category=
                            "SURVIVAL",

                        title=
                            "Team level position worsened after this death",

                        severity=
                            max(
                                int(
                                    severity
                                ),
                                3,
                            ),

                        minute=
                            minute,

                        source=
                            "critical_moment",

                        evidence=
                            moment,
                    )
                )

        return signals

    # ==================================================
    # POSITIVE MOMENTS
    # ==================================================

    def from_positive_moments(
        self,
        positive_moments,
    ):

        signals = []

        for moment in (
            positive_moments or []
        ):

            if not isinstance(
                moment,
                dict,
            ):
                continue

            reasons = set(
                moment.get(
                    "reasons",
                    [],
                )
                or []
            )

            impact_score = (
                moment.get(
                    "impact_score"
                )
                or 3
            )

            minute = (
                moment.get(
                    "minute"
                )
            )

            objective_conversion = (
                moment.get(
                    "objective_conversion"
                )
            )

            # Only emit a normalized positive coaching
            # signal when the combat event converted into
            # meaningful objective value.
            #
            # Ordinary kills/assists stay available in the
            # positive-moment evidence layer but don't
            # clutter the coaching signal layer.

            if (
                "objective_conversion"
                in reasons
                or
                objective_conversion
            ):

                signals.append(
                    self._signal(
                        key=
                            "successful_objective_conversion",

                        category=
                            "OBJECTIVES",

                        title=
                            "Successfully converted combat into an objective",

                        severity=
                            impact_score,

                        minute=
                            minute,

                        source=
                            "positive_moment",

                        positive=
                            True,

                        evidence=
                            moment,
                    )
                )

        return signals

    # ==================================================
    # RANK-RELATIVE PERFORMANCE
    # ==================================================

    RANK_METRICS = {

        "cs_at_10": {
            "key":
                "early_farming",

            "category":
                "FARMING",

            "positive_title":
                "Strong early farming",

            "negative_title":
                "Early farming below progression baseline",
        },

        "cs_per_min": {
            "key":
                "sustained_farming",

            "category":
                "FARMING",

            "positive_title":
                "Strong sustained farming",

            "negative_title":
                "Sustained farming below progression baseline",
        },

        "gold_at_10": {
            "key":
                "early_economy",

            "category":
                "ECONOMY",

            "positive_title":
                "Strong early economy",

            "negative_title":
                "Early economy below progression baseline",
        },

        "gold_per_min": {
            "key":
                "sustained_economy",

            "category":
                "ECONOMY",

            "positive_title":
                "Strong sustained economy",

            "negative_title":
                "Sustained economy below progression baseline",
        },

        "xp_at_10": {
            "key":
                "early_experience",

            "category":
                "ECONOMY",

            "positive_title":
                "Strong early experience progression",

            "negative_title":
                "Early experience below progression baseline",
        },

        "deaths": {
            "key":
                "survival_efficiency",

            "category":
                "SURVIVAL",

            "positive_title":
                "Strong survival compared with peers",

            "negative_title":
                "Survival below role baseline",
        },

        "kda": {
            "key":
                "combat_efficiency",

            "category":
                "COMBAT",

            "positive_title":
                "Strong combat efficiency",

            "negative_title":
                "Combat efficiency below role baseline",
        },
    }

    @staticmethod
    def _rank_signal_severity(
        percentile,
    ):
        """
        Convert rank-relative percentile into an
        internal evidence severity.

        This is NOT intended as a universal
        performance score.
        """

        if percentile is None:
            return 2

        percentile = float(
            percentile
        )

        if percentile < 10:
            return 5

        if percentile < 25:
            return 4

        if percentile < 40:
            return 3

        if percentile >= 90:
            return 5

        if percentile >= 75:
            return 4

        return 3

    def from_rank_performance(
        self,
        rank_performance,
    ):
        """
        Only metrics with supported rank trajectories
        become rank-development coaching signals.

        NOT_SUPPORTED metrics remain descriptive.
        """

        signals = []

        if not rank_performance:
            return signals

        # ==========================================
        # POSITIVE RANK-ALIGNED STRENGTHS
        # ==========================================

        for item in (
            rank_performance.get(
                "rank_aligned_strengths",
                [],
            )
            or []
        ):

            metric = (
                item.get(
                    "metric"
                )
            )

            config = (
                self.RANK_METRICS.get(
                    metric
                )
            )

            if config is None:
                continue

            peer_percentile = (
                item.get(
                    "peer_percentile"
                )
            )

            signals.append(
                self._signal(
                    key=
                        config[
                            "key"
                        ],

                    category=
                        config[
                            "category"
                        ],

                    title=
                        config[
                            "positive_title"
                        ],

                    severity=
                        self._rank_signal_severity(
                            peer_percentile
                        ),

                    source=
                        "rank_performance",

                    positive=
                        True,

                    evidence={
                        "metric":
                            metric,

                        "value":
                            item.get(
                                "value"
                            ),

                        "rank":
                            item.get(
                                "current_rank"
                            ),

                        "role":
                            item.get(
                                "role"
                            ),

                        "peer_percentile":
                            peer_percentile,

                        "peer_median":
                            item.get(
                                "peer_median"
                            ),

                        "next_rank":
                            item.get(
                                "next_rank"
                            ),

                        "next_rank_percentile":
                            item.get(
                                "next_rank_percentile"
                            ),

                        "rank_relevance":
                            item.get(
                                "rank_relevance"
                            ),

                        "trajectory_alignment":
                            item.get(
                                "trajectory_alignment"
                            ),

                        "trajectory_reliability":
                            item.get(
                                "trajectory_reliability"
                            ),
                    },
                )
            )

        # ==========================================
        # SUPPORTED DEVELOPMENT GAPS
        # ==========================================

        for item in (
            rank_performance.get(
                "development_opportunities",
                [],
            )
            or []
        ):

            metric = (
                item.get(
                    "metric"
                )
            )

            config = (
                self.RANK_METRICS.get(
                    metric
                )
            )

            if config is None:
                continue

            rank_relevance = (
                item.get(
                    "rank_relevance"
                )
            )

            # Only supported trajectory relationships
            # can become rank-development weaknesses.
            if (
                rank_relevance
                not in {
                    "STRONG",
                    "MODERATE",
                }
            ):
                continue

            next_percentile = (
                item.get(
                    "next_rank_percentile"
                )
            )

            peer_percentile = (
                item.get(
                    "peer_percentile"
                )
            )

            severity_basis = (
                next_percentile
                if (
                    next_percentile
                    is not None
                )
                else peer_percentile
            )

            signals.append(
                self._signal(
                    key=
                        config[
                            "key"
                        ],

                    category=
                        config[
                            "category"
                        ],

                    title=
                        config[
                            "negative_title"
                        ],

                    severity=
                        self._rank_signal_severity(
                            severity_basis
                        ),

                    source=
                        "rank_performance",

                    positive=
                        False,

                    evidence={
                        "metric":
                            metric,

                        "value":
                            item.get(
                                "value"
                            ),

                        "rank":
                            item.get(
                                "current_rank"
                            ),

                        "role":
                            item.get(
                                "role"
                            ),

                        "peer_percentile":
                            peer_percentile,

                        "peer_median":
                            item.get(
                                "peer_median"
                            ),

                        "next_rank":
                            item.get(
                                "next_rank"
                            ),

                        "next_rank_percentile":
                            next_percentile,

                        "rank_relevance":
                            rank_relevance,

                        "trajectory_alignment":
                            item.get(
                                "trajectory_alignment"
                            ),

                        "trajectory_reliability":
                            item.get(
                                "trajectory_reliability"
                            ),
                    },
                )
            )

        return signals