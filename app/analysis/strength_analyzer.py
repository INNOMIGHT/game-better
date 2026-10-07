from collections import defaultdict


class StrengthAnalyzer:

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

    def _recency_weight(
        self,
        match_index,
    ):

        return self.RECENCY_WEIGHTS.get(
            match_index,
            0.50,
        )

    def analyze(
        self,
        match_analyses,
    ):
        """
        match_analyses:
        newest -> oldest

        Positive coaching signals are aggregated
        across recent matches.
        """

        total_matches = len(
            match_analyses
        )

        buckets = defaultdict(
            lambda: {
                "title": None,
                "category": None,
                "occurrences": 0,
                "weighted_occurrences": 0.0,
                "impact_total": 0,
                "matches": set(),
                "minutes": [],
                "examples": [],
            }
        )

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

                if not signal.get(
                    "positive",
                    False,
                ):
                    continue

                key = signal.get(
                    "key"
                )

                if not key:
                    continue

                bucket = buckets[
                    key
                ]

                bucket["title"] = (
                    bucket["title"]
                    or signal.get(
                        "title"
                    )
                )

                bucket["category"] = (
                    bucket["category"]
                    or signal.get(
                        "category"
                    )
                )

                severity = signal.get(
                    "severity",
                    1,
                )

                bucket[
                    "occurrences"
                ] += 1

                bucket[
                    "weighted_occurrences"
                ] += recency_weight

                bucket[
                    "impact_total"
                ] += severity

                if match_id:

                    bucket[
                        "matches"
                    ].add(
                        match_id
                    )

                minute = signal.get(
                    "minute"
                )

                if minute is not None:

                    bucket[
                        "minutes"
                    ].append(
                        minute
                    )

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

                        "impact":
                            severity,

                        "evidence":
                            signal.get(
                                "evidence",
                                {},
                            ),
                    })

        strengths = []

        for key, data in (
            buckets.items()
        ):

            matches_affected = len(
                data["matches"]
            )

            frequency = (
                matches_affected
                / total_matches
                if total_matches
                else 0
            )

            average_impact = (
                data["impact_total"]
                / data["occurrences"]
                if data["occurrences"]
                else 0
            )

            average_recency = (
                data[
                    "weighted_occurrences"
                ]
                / data[
                    "occurrences"
                ]
                if data[
                    "occurrences"
                ]
                else 0
            )

            strength_score = (
                0.50
                * min(
                    frequency,
                    1.0,
                )
                +
                0.30
                * min(
                    average_impact
                    / 5.0,
                    1.0,
                )
                +
                0.20
                * min(
                    average_recency,
                    1.0,
                )
            )

            confidence = (
                self._confidence(
                    matches_affected,
                    total_matches,
                    data[
                        "occurrences"
                    ],
                )
            )

            strengths.append({
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

                "score":
                    round(
                        strength_score,
                        3,
                    ),

                "confidence":
                    confidence,

                "occurrences":
                    data[
                        "occurrences"
                    ],

                "matches_affected":
                    matches_affected,

                "matches_analyzed":
                    total_matches,

                "match_frequency":
                    round(
                        frequency,
                        3,
                    ),

                "average_impact":
                    round(
                        average_impact,
                        2,
                    ),

                "examples":
                    data[
                        "examples"
                    ],
            })

        strengths.sort(
            key=lambda item:
                item["score"],
            reverse=True,
        )

        return {
            "matches_analyzed":
                total_matches,

            "strength_count":
                len(
                    strengths
                ),

            "strengths":
                strengths,
        }

    @staticmethod
    def _confidence(
        matches_affected,
        total_matches,
        occurrences,
    ):

        if not total_matches:
            return "LOW"

        frequency = (
            matches_affected
            / total_matches
        )

        if (
            matches_affected >= 5
            and
            frequency >= 0.40
            and
            occurrences >= 5
        ):
            return "HIGH"

        if (
            matches_affected >= 3
            and
            frequency >= 0.25
        ):
            return "MEDIUM"

        return "LOW"