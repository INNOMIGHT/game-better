from collections import defaultdict


class WeaknessAnalyzer:

    RECENCY_WEIGHTS = {
        0: 1.00,
        1: 0.95,
        2: 0.90,
        3: 0.85,
        4: 0.80,
        5: 0.75,
        6: 0.70,
        7: 0.65,
        8: 0.60,
        9: 0.55,
    }

    # --------------------------------------------------
    # RECENCY
    # --------------------------------------------------

    def _recency_weight(
        self,
        match_index,
    ):

        return self.RECENCY_WEIGHTS.get(
            match_index,
            0.50,
        )

    # --------------------------------------------------
    # MAIN ANALYSIS
    # --------------------------------------------------

    def analyze(
        self,
        match_analyses,
    ):
        """
        Analyze recurring negative coaching signals
        across recent matches.

        match_analyses MUST be ordered:

            newest -> oldest

        Expected simplified shape:

        [
            {
                "match_id": "...",

                "coaching_signals": [
                    {
                        "key": "farm_recovery_failure",
                        "category": "FARMING",
                        "title": "...",
                        "severity": 4,
                        "minute": 18.4,
                        "positive": False,
                        "source": "FarmingDisruptionDetector",
                        "evidence": {...}
                    }
                ]
            }
        ]

        Positive signals are intentionally ignored here.
        They are handled by StrengthAnalyzer.
        """

        weakness_data = defaultdict(
            lambda: {

                # ----------------------------------
                # Metadata
                # ----------------------------------

                "title": None,
                "category": None,

                # ----------------------------------
                # Frequency / severity
                # ----------------------------------

                "occurrences": 0,

                "weighted_occurrences": 0.0,

                "severity_total": 0,

                "high_impact_occurrences": 0,

                # ----------------------------------
                # Match coverage
                # ----------------------------------

                "matches": set(),

                # ----------------------------------
                # Timing
                # ----------------------------------

                "minutes": [],

                # ----------------------------------
                # Optional economic consequence
                # ----------------------------------

                "gold_consequence_total": 0,

                "gold_consequence_samples": 0,

                # ----------------------------------
                # Evidence examples
                # ----------------------------------

                "examples": [],
            }
        )

        total_matches = len(
            match_analyses
        )

        # ==================================================
        # COLLECT SIGNALS
        # ==================================================

        for match_index, analysis in enumerate(
            match_analyses
        ):

            recency_weight = (
                self._recency_weight(
                    match_index
                )
            )

            match_id = analysis.get(
                "match_id"
            )

            signals = analysis.get(
                "coaching_signals",
                [],
            )

            for signal in signals:

                # ----------------------------------
                # WeaknessAnalyzer only processes
                # NEGATIVE signals.
                # ----------------------------------

                if signal.get(
                    "positive",
                    False,
                ):
                    continue

                key = signal.get(
                    "key"
                )

                if not key:
                    continue

                bucket = weakness_data[
                    key
                ]

                # ----------------------------------
                # Store metadata
                # ----------------------------------

                if (
                    bucket["title"]
                    is None
                ):

                    bucket["title"] = (
                        signal.get(
                            "title"
                        )
                    )

                if (
                    bucket["category"]
                    is None
                ):

                    bucket["category"] = (
                        signal.get(
                            "category"
                        )
                    )

                # ----------------------------------
                # Severity
                # ----------------------------------

                severity = signal.get(
                    "severity",
                    1,
                )

                try:

                    severity = float(
                        severity
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    severity = 1.0

                severity = max(
                    1.0,
                    min(
                        severity,
                        5.0,
                    ),
                )

                # ----------------------------------
                # Occurrence counts
                # ----------------------------------

                bucket[
                    "occurrences"
                ] += 1

                bucket[
                    "weighted_occurrences"
                ] += recency_weight

                bucket[
                    "severity_total"
                ] += severity

                if severity >= 4:

                    bucket[
                        "high_impact_occurrences"
                    ] += 1

                # ----------------------------------
                # Match coverage
                # ----------------------------------

                if match_id:

                    bucket[
                        "matches"
                    ].add(
                        match_id
                    )

                # ----------------------------------
                # Timing
                # ----------------------------------

                minute = signal.get(
                    "minute"
                )

                if minute is not None:

                    try:

                        bucket[
                            "minutes"
                        ].append(
                            float(
                                minute
                            )
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        pass

                # ----------------------------------
                # Evidence
                # ----------------------------------

                evidence = (
                    signal.get(
                        "evidence",
                        {}
                    )
                    or {}
                )

                gold_change = (
                    evidence.get(
                        "gold_difference_change"
                    )
                )

                if gold_change is not None:

                    try:

                        gold_change = float(
                            gold_change
                        )

                        bucket[
                            "gold_consequence_total"
                        ] += gold_change

                        bucket[
                            "gold_consequence_samples"
                        ] += 1

                    except (
                        TypeError,
                        ValueError,
                    ):

                        pass

                # ----------------------------------
                # Keep a few examples for UI /
                # recommendation evidence.
                # ----------------------------------

                if (
                    len(
                        bucket[
                            "examples"
                        ]
                    )
                    < 3
                ):

                    bucket[
                        "examples"
                    ].append({

                        "match_id":
                            match_id,

                        "minute":
                            minute,

                        "severity":
                            round(
                                severity,
                                2,
                            ),

                        "signal":
                            key,

                        "source":
                            signal.get(
                                "source"
                            ),

                        "evidence":
                            evidence,
                    })

        # ==================================================
        # SCORE WEAKNESSES
        # ==================================================

        weaknesses = []

        for key, data in (
            weakness_data.items()
        ):

            occurrences = (
                data[
                    "occurrences"
                ]
            )

            if occurrences <= 0:
                continue

            # ----------------------------------
            # How many different matches showed
            # this weakness?
            # ----------------------------------

            matches_affected = len(
                data[
                    "matches"
                ]
            )

            match_frequency = (
                matches_affected
                / total_matches
                if total_matches
                else 0
            )

            # ----------------------------------
            # Average severity
            # ----------------------------------

            average_severity = (
                data[
                    "severity_total"
                ]
                / occurrences
            )

            # ----------------------------------
            # Average timing
            # ----------------------------------

            average_minute = None

            if data["minutes"]:

                average_minute = (
                    sum(
                        data[
                            "minutes"
                        ]
                    )
                    / len(
                        data[
                            "minutes"
                        ]
                    )
                )

            # ----------------------------------
            # Optional average economic impact
            # ----------------------------------

            average_gold_change = None

            if (
                data[
                    "gold_consequence_samples"
                ]
                > 0
            ):

                average_gold_change = (
                    data[
                        "gold_consequence_total"
                    ]
                    / data[
                        "gold_consequence_samples"
                    ]
                )

            # ==================================================
            # COMPONENT SCORES
            # ==================================================

            # Recurrence:
            #
            # weakness happening in 7/10 games
            # should matter more than one isolated event.

            recurrence_score = min(
                match_frequency,
                1.0,
            )

            # Severity:
            #
            # Average severity 5 -> 1.0
            # Average severity 2.5 -> 0.5

            severity_score = min(
                average_severity
                / 5.0,
                1.0,
            )

            # Recency:
            #
            # Recent occurrences matter slightly more.

            recency_score = min(
                data[
                    "weighted_occurrences"
                ]
                / occurrences,
                1.0,
            )

            # ==================================================
            # FINAL WEAKNESS SCORE
            # ==================================================

            weakness_score = (
                0.45
                * recurrence_score
                +
                0.35
                * severity_score
                +
                0.20
                * recency_score
            )

            confidence = (
                self._confidence_label(
                    matches_affected=
                        matches_affected,

                    total_matches=
                        total_matches,

                    occurrences=
                        occurrences,
                )
            )

            weaknesses.append({

                # ----------------------------------
                # Identity
                # ----------------------------------

                "key":
                    key,

                "title":
                    data[
                        "title"
                    ]
                    or key,

                "category":
                    data[
                        "category"
                    ]
                    or "GENERAL",

                # ----------------------------------
                # Ranking
                # ----------------------------------

                "score":
                    round(
                        weakness_score,
                        3,
                    ),

                "confidence":
                    confidence,

                # ----------------------------------
                # Frequency
                # ----------------------------------

                "occurrences":
                    occurrences,

                "matches_affected":
                    matches_affected,

                "matches_analyzed":
                    total_matches,

                "match_frequency":
                    round(
                        match_frequency,
                        3,
                    ),

                # ----------------------------------
                # Impact
                # ----------------------------------

                "average_severity":
                    round(
                        average_severity,
                        2,
                    ),

                "high_impact_occurrences":
                    data[
                        "high_impact_occurrences"
                    ],

                # ----------------------------------
                # Timing
                # ----------------------------------

                "average_minute":
                    (
                        round(
                            average_minute,
                            1,
                        )
                        if average_minute
                        is not None
                        else None
                    ),

                # ----------------------------------
                # Economic consequence
                # ----------------------------------

                "average_gold_difference_change":
                    (
                        round(
                            average_gold_change,
                            0,
                        )
                        if average_gold_change
                        is not None
                        else None
                    ),

                # ----------------------------------
                # UI evidence
                # ----------------------------------

                "examples":
                    data[
                        "examples"
                    ],
            })

        # Highest-priority weakness first.

        weaknesses.sort(
            key=lambda item:
                item[
                    "score"
                ],
            reverse=True,
        )

        return {

            "matches_analyzed":
                total_matches,

            "weakness_count":
                len(
                    weaknesses
                ),

            "weaknesses":
                weaknesses,
        }

    # ==================================================
    # CONFIDENCE
    # ==================================================

    @staticmethod
    def _confidence_label(
        matches_affected,
        total_matches,
        occurrences,
    ):

        if total_matches <= 0:

            return "LOW"

        frequency = (
            matches_affected
            / total_matches
        )

        # Strong recurring evidence.

        if (
            matches_affected >= 5
            and
            frequency >= 0.40
            and
            occurrences >= 5
        ):

            return "HIGH"

        # Some recurring evidence.

        if (
            matches_affected >= 3
            and
            frequency >= 0.25
        ):

            return "MEDIUM"

        # Mostly isolated / insufficient evidence.

        return "LOW"