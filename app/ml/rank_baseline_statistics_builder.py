from pathlib import Path

import pandas as pd


FEATURE_DIR = Path(
    "artifacts/rank_baseline/features"
)

OUTPUT_DIR = Path(
    "artifacts/rank_baseline/statistics"
)


class RankBaselineStatisticsBuilder:

    METRICS = [
        # -----------------------------
        # Early game
        # -----------------------------
        "gold_at_10",
        "xp_at_10",
        "cs_at_10",
        "level_at_10",

        "cs_per_min_at_10",
        "gold_per_min_at_10",
        "xp_per_min_at_10",

        # -----------------------------
        # Full match
        # -----------------------------
        "cs_per_min",
        "gold_per_min",

        # -----------------------------
        # Combat
        # -----------------------------
        "kills",
        "deaths",
        "assists",
        "kda",
    ]

    VALID_ROLES = {
        "TOP",
        "JUNGLE",
        "MIDDLE",
        "BOTTOM",
        "UTILITY",
    }

    # ==========================================
    # SAMPLE CONFIDENCE
    # ==========================================

    @staticmethod
    def _sample_confidence(
        sample_count,
    ):

        if sample_count >= 100:
            return "HIGH"

        if sample_count >= 50:
            return "MEDIUM"

        if sample_count >= 25:
            return "LOW"

        return "VERY_LOW"

    # ==========================================
    # BUILD ONE METRIC STAT
    # ==========================================

    def _metric_statistics(
        self,
        *,
        tier,
        role,
        metric,
        values,
    ):

        values = (
            values
            .dropna()
            .astype(float)
        )

        if values.empty:
            return None

        sample_count = len(
            values
        )

        return {
            "rank_bucket":
                tier,

            "role":
                role,

            "metric":
                metric,

            "sample_count":
                sample_count,

            "confidence":
                self._sample_confidence(
                    sample_count
                ),

            "mean":
                round(
                    values.mean(),
                    4,
                ),

            "std":
                round(
                    values.std(),
                    4,
                ),

            "min":
                round(
                    values.min(),
                    4,
                ),

            "p10":
                round(
                    values.quantile(
                        0.10
                    ),
                    4,
                ),

            "p25":
                round(
                    values.quantile(
                        0.25
                    ),
                    4,
                ),

            "p50":
                round(
                    values.quantile(
                        0.50
                    ),
                    4,
                ),

            "p75":
                round(
                    values.quantile(
                        0.75
                    ),
                    4,
                ),

            "p90":
                round(
                    values.quantile(
                        0.90
                    ),
                    4,
                ),

            "max":
                round(
                    values.max(),
                    4,
                ),
        }

    # ==========================================
    # BUILD TIER
    # ==========================================

    def build(
        self,
        tier,
    ):

        tier = tier.upper()

        input_path = (
            FEATURE_DIR
            / f"{tier}_participant_features.csv"
        )

        if not input_path.exists():

            raise FileNotFoundError(
                f"Participant feature dataset "
                f"not found: {input_path}"
            )

        df = pd.read_csv(
            input_path
        )

        if df.empty:

            raise RuntimeError(
                f"No participant features found "
                f"for {tier}."
            )

        # ------------------------------------------
        # Keep valid Riot role labels only.
        # ------------------------------------------

        df = df[
            df[
                "role"
            ].isin(
                self.VALID_ROLES
            )
        ].copy()

        rows = []

        # ==========================================
        # ROLE-SPECIFIC DISTRIBUTIONS
        # ==========================================

        for role in sorted(
            self.VALID_ROLES
        ):

            role_df = df[
                df[
                    "role"
                ]
                == role
            ]

            if role_df.empty:
                continue

            for metric in self.METRICS:

                if (
                    metric
                    not in role_df.columns
                ):
                    continue

                result = (
                    self._metric_statistics(
                        tier=tier,
                        role=role,
                        metric=metric,
                        values=
                            role_df[
                                metric
                            ],
                    )
                )

                if result is not None:

                    rows.append(
                        result
                    )

        stats_df = (
            pd.DataFrame(
                rows
            )
        )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            OUTPUT_DIR
            / f"{tier}_role_statistics.csv"
        )

        stats_df.to_csv(
            output_path,
            index=False,
        )

        # ==========================================
        # REPORT
        # ==========================================

        print()
        print(
            f"{tier} ROLE BASELINE STATISTICS"
        )

        print(
            "=" * 42
        )

        print(
            f"Participant rows: "
            f"{len(df)}"
        )

        print(
            f"Statistics rows: "
            f"{len(stats_df)}"
        )

        print()

        print(
            "ROLE SAMPLE COUNTS"
        )

        print(
            df[
                "role"
            ].value_counts()
        )

        # ==========================================
        # Useful preview
        # ==========================================

        preview_metrics = {
            "cs_at_10",
            "gold_at_10",
            "xp_at_10",
            "cs_per_min",
            "gold_per_min",
            "deaths",
            "kda",
        }

        preview = stats_df[
            stats_df[
                "metric"
            ].isin(
                preview_metrics
            )
        ].copy()

        if not preview.empty:

            print()
            print(
                "KEY BASELINES"
            )

            print(
                preview[
                    [
                        "role",
                        "metric",
                        "sample_count",
                        "confidence",
                        "p25",
                        "p50",
                        "p75",
                        "p90",
                    ]
                ]
                .sort_values(
                    [
                        "role",
                        "metric",
                    ]
                )
                .to_string(
                    index=False
                )
            )

        print()
        print(
            f"Saved: "
            f"{output_path}"
        )

        return stats_df