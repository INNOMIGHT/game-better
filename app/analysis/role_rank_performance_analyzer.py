from pathlib import Path

import pandas as pd


STATISTICS_DIR = Path(
    "artifacts/rank_baseline/statistics"
)

TRAJECTORY_PATH = Path(
    "artifacts/rank_baseline/trajectories/"
    "GOLD_to_DIAMOND_trajectories.csv"
)


class RoleRankPerformanceAnalyzer:

    RANKS = [
        "GOLD",
        "PLATINUM",
        "EMERALD",
        "DIAMOND",
    ]

    RANK_INDEX = {
        rank: index
        for index, rank in enumerate(
            RANKS
        )
    }

    # ==================================================
    # METRIC SEMANTICS
    # ==================================================

    METRIC_DIRECTION = {
        "cs_at_10":
            "HIGHER_BETTER",

        "gold_at_10":
            "HIGHER_BETTER",

        "xp_at_10":
            "HIGHER_BETTER",

        "level_at_10":
            "HIGHER_BETTER",

        "cs_per_min_at_10":
            "HIGHER_BETTER",

        "gold_per_min_at_10":
            "HIGHER_BETTER",

        "xp_per_min_at_10":
            "HIGHER_BETTER",

        "cs_per_min":
            "HIGHER_BETTER",

        "gold_per_min":
            "HIGHER_BETTER",

        "kills":
            "HIGHER_BETTER",

        "assists":
            "HIGHER_BETTER",

        "kda":
            "HIGHER_BETTER",

        "deaths":
            "LOWER_BETTER",
    }

    # Keep as ordered tuple rather than set.
    #
    # This gives deterministic output ordering.
    COACHING_METRICS = (
        "cs_at_10",
        "gold_at_10",
        "xp_at_10",
        "cs_per_min",
        "gold_per_min",
        "deaths",
        "kda",
    )

    def __init__(
        self,
    ):

        self._statistics_cache = {}

        self.trajectories = (
            self._load_trajectories()
        )

    # ==================================================
    # LOADERS
    # ==================================================

    def _load_statistics(
        self,
        rank,
    ):

        rank = rank.upper()

        if (
            rank
            in self._statistics_cache
        ):
            return (
                self._statistics_cache[
                    rank
                ]
            )

        path = (
            STATISTICS_DIR
            / f"{rank}_role_statistics.csv"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Missing baseline statistics: "
                f"{path}"
            )

        df = pd.read_csv(
            path
        )

        self._statistics_cache[
            rank
        ] = df

        return df

    @staticmethod
    def _load_trajectories():

        if not TRAJECTORY_PATH.exists():

            raise FileNotFoundError(
                "Missing rank trajectory file: "
                f"{TRAJECTORY_PATH}"
            )

        return pd.read_csv(
            TRAJECTORY_PATH
        )

    # ==================================================
    # RANK HELPERS
    # ==================================================

    def _next_rank(
        self,
        rank,
    ):

        rank = rank.upper()

        index = (
            self.RANK_INDEX.get(
                rank
            )
        )

        if index is None:
            return None

        if (
            index
            >= len(
                self.RANKS
            ) - 1
        ):
            return None

        return (
            self.RANKS[
                index + 1
            ]
        )

    # ==================================================
    # BASELINE LOOKUPS
    # ==================================================

    def _get_baseline_row(
        self,
        *,
        rank,
        role,
        metric,
    ):

        df = (
            self._load_statistics(
                rank
            )
        )

        rows = df[
            (
                df[
                    "role"
                ]
                == role
            )
            &
            (
                df[
                    "metric"
                ]
                == metric
            )
        ]

        if rows.empty:
            return None

        return (
            rows.iloc[0]
        )

    def _get_trajectory(
        self,
        *,
        role,
        metric,
    ):

        rows = (
            self.trajectories[
                (
                    self.trajectories[
                        "role"
                    ]
                    == role
                )
                &
                (
                    self.trajectories[
                        "metric"
                    ]
                    == metric
                )
            ]
        )

        if rows.empty:
            return None

        return (
            rows.iloc[0]
        )

    # ==================================================
    # PERCENTILE ESTIMATION
    # ==================================================

    @staticmethod
    def _raw_percentile(
        value,
        row,
    ):
        """
        Approximate empirical percentile using:

        min
        p10
        p25
        p50
        p75
        p90
        max

        Piecewise-linear interpolation is used
        between stored quantile boundaries.

        This is an approximation, not the full ECDF.
        """

        points = [
            (
                float(
                    row[
                        "min"
                    ]
                ),
                0.0,
            ),

            (
                float(
                    row[
                        "p10"
                    ]
                ),
                10.0,
            ),

            (
                float(
                    row[
                        "p25"
                    ]
                ),
                25.0,
            ),

            (
                float(
                    row[
                        "p50"
                    ]
                ),
                50.0,
            ),

            (
                float(
                    row[
                        "p75"
                    ]
                ),
                75.0,
            ),

            (
                float(
                    row[
                        "p90"
                    ]
                ),
                90.0,
            ),

            (
                float(
                    row[
                        "max"
                    ]
                ),
                100.0,
            ),
        ]

        if (
            value
            <= points[0][0]
        ):
            return 0.0

        if (
            value
            >= points[-1][0]
        ):
            return 100.0

        for index in range(
            1,
            len(points),
        ):

            (
                low_value,
                low_percentile,
            ) = (
                points[
                    index - 1
                ]
            )

            (
                high_value,
                high_percentile,
            ) = (
                points[
                    index
                ]
            )

            if (
                value
                <= high_value
            ):

                # Integer metrics may have flat
                # quantile boundaries.
                if (
                    high_value
                    == low_value
                ):

                    return (
                        high_percentile
                    )

                fraction = (
                    (
                        value
                        - low_value
                    )
                    /
                    (
                        high_value
                        - low_value
                    )
                )

                return (
                    low_percentile
                    +
                    fraction
                    *
                    (
                        high_percentile
                        - low_percentile
                    )
                )

        return 100.0

    def _performance_percentile(
        self,
        *,
        metric,
        value,
        baseline_row,
    ):

        raw = (
            self._raw_percentile(
                value=
                    value,

                row=
                    baseline_row,
            )
        )

        direction = (
            self.METRIC_DIRECTION.get(
                metric,
                "HIGHER_BETTER",
            )
        )

        if (
            direction
            == "LOWER_BETTER"
        ):

            return (
                100.0
                - raw
            )

        return raw

    # ==================================================
    # TRAJECTORY
    # ==================================================

    @staticmethod
    def _trajectory_reliability(
        trajectory,
    ):

        if trajectory is None:
            return "UNKNOWN"

        confidence = (
            trajectory[
                "trajectory_confidence"
            ]
        )

        monotonicity = float(
            trajectory[
                "monotonicity_score"
            ]
        )

        if (
            confidence
            == "VERY_LOW"
        ):
            return "VERY_LOW"

        if (
            monotonicity
            >= 0.99
        ):
            return "STRONG"

        if (
            monotonicity
            >= 0.66
        ):
            return "MODERATE"

        return "WEAK"

    def _trajectory_alignment(
        self,
        *,
        metric,
        trajectory,
    ):
        """
        Does the observed rank trajectory move in
        the same direction as our metric semantics?

        Example:

        CS/min:
            HIGHER_BETTER
            rank trajectory INCREASING
            -> ALIGNED

        KDA:
            HIGHER_BETTER
            rank trajectory DECREASING
            -> OPPOSED
        """

        if trajectory is None:
            return "UNKNOWN"

        observed_direction = (
            trajectory[
                "overall_direction"
            ]
        )

        expected_direction = (
            self.METRIC_DIRECTION.get(
                metric
            )
        )

        if (
            observed_direction
            == "FLAT"
        ):
            return "FLAT"

        if (
            expected_direction
            == "HIGHER_BETTER"
        ):

            if (
                observed_direction
                == "INCREASING"
            ):
                return "ALIGNED"

            return "OPPOSED"

        if (
            expected_direction
            == "LOWER_BETTER"
        ):

            if (
                observed_direction
                == "DECREASING"
            ):
                return "ALIGNED"

            return "OPPOSED"

        return "UNKNOWN"

    def _rank_relevance(
        self,
        *,
        metric,
        trajectory,
    ):
        """
        Conservative measure for whether a metric
        should influence rank-development coaching.

        This is NOT causal importance.
        """

        if trajectory is None:
            return "UNKNOWN"

        reliability = (
            self._trajectory_reliability(
                trajectory
            )
        )

        alignment = (
            self._trajectory_alignment(
                metric=
                    metric,

                trajectory=
                    trajectory,
            )
        )

        confidence = (
            trajectory[
                "trajectory_confidence"
            ]
        )

        if (
            confidence
            == "VERY_LOW"
        ):
            return "INSUFFICIENT_DATA"

        if (
            alignment
            == "OPPOSED"
        ):
            return "NOT_SUPPORTED"

        if (
            alignment
            == "FLAT"
        ):
            return "WEAK"

        if (
            alignment
            != "ALIGNED"
        ):
            return "UNKNOWN"

        if (
            reliability
            == "STRONG"
        ):
            return "STRONG"

        if (
            reliability
            == "MODERATE"
        ):
            return "MODERATE"

        return "WEAK"

    # ==================================================
    # STATUS
    # ==================================================

    @staticmethod
    def _peer_status(
        percentile,
    ):

        if percentile >= 75:
            return "STRENGTH"

        if percentile >= 55:
            return "ABOVE_AVERAGE"

        if percentile >= 40:
            return "AVERAGE"

        if percentile >= 25:
            return "BELOW_AVERAGE"

        return "WEAKNESS"

    @staticmethod
    def _next_rank_status(
        percentile,
    ):

        if percentile >= 75:
            return "STRONG_VS_NEXT_RANK"

        if percentile >= 50:
            return "NEXT_RANK_COMPETITIVE"

        if percentile >= 25:
            return "APPROACHING_NEXT_RANK"

        return "BELOW_NEXT_RANK"

    # ==================================================
    # SINGLE METRIC
    # ==================================================

    def analyze_metric(
        self,
        *,
        rank,
        role,
        metric,
        value,
    ):

        rank = rank.upper()

        role = role.upper()

        if (
            metric
            not in self.COACHING_METRICS
        ):
            return None

        # ==========================================
        # CURRENT RANK
        # ==========================================

        current_baseline = (
            self._get_baseline_row(
                rank=
                    rank,

                role=
                    role,

                metric=
                    metric,
            )
        )

        if current_baseline is None:
            return None

        current_percentile = (
            self._performance_percentile(
                metric=
                    metric,

                value=
                    value,

                baseline_row=
                    current_baseline,
            )
        )

        # ==========================================
        # NEXT RANK
        # ==========================================

        next_rank = (
            self._next_rank(
                rank
            )
        )

        next_rank_percentile = None

        next_rank_confidence = None

        next_rank_sample_count = None

        next_status = None

        if (
            next_rank
            is not None
        ):

            next_baseline = (
                self._get_baseline_row(
                    rank=
                        next_rank,

                    role=
                        role,

                    metric=
                        metric,
                )
            )

            if (
                next_baseline
                is not None
            ):

                next_rank_percentile = (
                    self._performance_percentile(
                        metric=
                            metric,

                        value=
                            value,

                        baseline_row=
                            next_baseline,
                    )
                )

                next_rank_confidence = (
                    next_baseline[
                        "confidence"
                    ]
                )

                next_rank_sample_count = int(
                    next_baseline[
                        "sample_count"
                    ]
                )

                next_status = (
                    self._next_rank_status(
                        next_rank_percentile
                    )
                )

        # ==========================================
        # TRAJECTORY
        # ==========================================

        trajectory = (
            self._get_trajectory(
                role=
                    role,

                metric=
                    metric,
            )
        )

        trajectory_reliability = (
            self._trajectory_reliability(
                trajectory
            )
        )

        trajectory_alignment = (
            self._trajectory_alignment(
                metric=
                    metric,

                trajectory=
                    trajectory,
            )
        )

        rank_relevance = (
            self._rank_relevance(
                metric=
                    metric,

                trajectory=
                    trajectory,
            )
        )

        # ==========================================
        # RESULT
        # ==========================================

        result = {
            "metric":
                metric,

            "value":
                round(
                    float(
                        value
                    ),
                    4,
                ),

            "direction":
                self.METRIC_DIRECTION[
                    metric
                ],

            "current_rank":
                rank,

            "role":
                role,

            # ----------------------------------
            # Peer comparison
            # ----------------------------------

            "peer_percentile":
                round(
                    current_percentile,
                    1,
                ),

            "peer_status":
                self._peer_status(
                    current_percentile
                ),

            "peer_sample_count":
                int(
                    current_baseline[
                        "sample_count"
                    ]
                ),

            "peer_confidence":
                current_baseline[
                    "confidence"
                ],

            "peer_median":
                float(
                    current_baseline[
                        "p50"
                    ]
                ),

            # ----------------------------------
            # Next rank
            # ----------------------------------

            "next_rank":
                next_rank,

            "next_rank_percentile":
                (
                    round(
                        next_rank_percentile,
                        1,
                    )
                    if (
                        next_rank_percentile
                        is not None
                    )
                    else None
                ),

            "next_rank_status":
                next_status,

            "next_rank_confidence":
                next_rank_confidence,

            "next_rank_sample_count":
                next_rank_sample_count,

            # ----------------------------------
            # Rank trajectory
            # ----------------------------------

            "trajectory_reliability":
                trajectory_reliability,

            "trajectory_alignment":
                trajectory_alignment,

            "rank_relevance":
                rank_relevance,
        }

        if (
            trajectory
            is not None
        ):

            percent_change = (
                trajectory[
                    "percent_change"
                ]
            )

            result[
                "trajectory"
            ] = {
                "gold":
                    float(
                        trajectory[
                            "gold_p50"
                        ]
                    ),

                "platinum":
                    float(
                        trajectory[
                            "platinum_p50"
                        ]
                    ),

                "emerald":
                    float(
                        trajectory[
                            "emerald_p50"
                        ]
                    ),

                "diamond":
                    float(
                        trajectory[
                            "diamond_p50"
                        ]
                    ),

                "overall_direction":
                    trajectory[
                        "overall_direction"
                    ],

                "monotonicity":
                    round(
                        float(
                            trajectory[
                                "monotonicity_score"
                            ]
                        ),
                        3,
                    ),

                "direction_changes":
                    int(
                        trajectory[
                            "direction_changes"
                        ]
                    ),

                "gold_to_diamond_change_pct":
                    (
                        round(
                            float(
                                percent_change
                            ),
                            2,
                        )
                        if not pd.isna(
                            percent_change
                        )
                        else None
                    ),

                "confidence":
                    trajectory[
                        "trajectory_confidence"
                    ],
            }

        return result

    # ==================================================
    # FULL ANALYSIS
    # ==================================================

    def analyze(
        self,
        *,
        rank,
        role,
        features,
    ):

        rank = rank.upper()

        role = role.upper()

        results = []

        # ==========================================
        # ANALYZE METRICS
        # ==========================================

        for metric in (
            self.COACHING_METRICS
        ):

            value = (
                features.get(
                    metric
                )
            )

            if value is None:
                continue

            result = (
                self.analyze_metric(
                    rank=
                        rank,

                    role=
                        role,

                    metric=
                        metric,

                    value=
                        value,
                )
            )

            if result is not None:

                results.append(
                    result
                )

        # ==========================================
        # PEER STRENGTHS
        #
        # These describe player performance.
        # They do NOT require rank relevance.
        # ==========================================

        strengths = [
            item
            for item in results
            if (
                item[
                    "peer_percentile"
                ]
                >= 75
            )
        ]

        strengths.sort(
            key=lambda item:
                item[
                    "peer_percentile"
                ],
            reverse=True,
        )

        # ==========================================
        # PEER WEAKNESSES
        # ==========================================

        weaknesses = [
            item
            for item in results
            if (
                item[
                    "peer_percentile"
                ]
                < 40
            )
        ]

        weaknesses.sort(
            key=lambda item:
                item[
                    "peer_percentile"
                ]
        )

        # ==========================================
        # NEXT-RANK READY
        #
        # Descriptive comparison only.
        #
        # A metric can be next-rank competitive
        # without being a proven rank separator.
        # ==========================================

        next_rank_ready = [
            item
            for item in results
            if (
                item[
                    "next_rank_percentile"
                ]
                is not None
                and
                item[
                    "next_rank_percentile"
                ]
                >= 50
            )
        ]

        next_rank_ready.sort(
            key=lambda item:
                item[
                    "next_rank_percentile"
                ],
            reverse=True,
        )

        # ==========================================
        # RANK-ALIGNED STRENGTHS
        #
        # Stronger evidence that this skill is
        # both good AND associated with progression.
        # ==========================================

        rank_aligned_strengths = [
            item
            for item in results
            if (
                item[
                    "peer_percentile"
                ]
                >= 60
                and
                item[
                    "rank_relevance"
                ]
                in {
                    "STRONG",
                    "MODERATE",
                }
            )
        ]

        rank_aligned_strengths.sort(
            key=lambda item: (
                item[
                    "peer_percentile"
                ],
                item[
                    "next_rank_percentile"
                ]
                if (
                    item[
                        "next_rank_percentile"
                    ]
                    is not None
                )
                else 0,
            ),
            reverse=True,
        )

        # ==========================================
        # DEVELOPMENT OPPORTUNITIES
        #
        # These MUST be:
        #
        # 1. below next-rank median
        # 2. supported by the multi-rank trend
        # 3. not VERY_LOW data
        #
        # This prevents KDA-style false advice.
        # ==========================================

        development = []

        for item in results:

            next_percentile = (
                item[
                    "next_rank_percentile"
                ]
            )

            if (
                next_percentile
                is None
            ):
                continue

            if (
                next_percentile
                >= 50
            ):
                continue

            if (
                item[
                    "rank_relevance"
                ]
                not in {
                    "STRONG",
                    "MODERATE",
                }
            ):
                continue

            development.append(
                item
            )

        development.sort(
            key=lambda item: (
                item[
                    "next_rank_percentile"
                ],
                item[
                    "peer_percentile"
                ],
            )
        )

        # ==========================================
        # DESCRIPTIVE ONLY
        #
        # Interesting metrics which should NOT
        # currently become rank-up advice.
        # ==========================================

        descriptive_only = [
            item
            for item in results
            if (
                item[
                    "rank_relevance"
                ]
                in {
                    "NOT_SUPPORTED",
                    "INSUFFICIENT_DATA",
                    "WEAK",
                }
            )
        ]

        return {
            "rank":
                rank,

            "role":
                role,

            "metrics":
                results,

            "strengths":
                strengths[
                    ::
                ],

            "weaknesses":
                weaknesses[
                    ::
                ],

            "next_rank_ready":
                next_rank_ready[
                    ::
                ],

            "rank_aligned_strengths":
                rank_aligned_strengths[
                    ::
                ],

            "development_opportunities":
                development[
                    ::
                ],

            "descriptive_only":
                descriptive_only,
        }