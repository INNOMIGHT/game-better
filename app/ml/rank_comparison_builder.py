from pathlib import Path

import pandas as pd


STATISTICS_DIR = Path(
    "artifacts/rank_baseline/statistics"
)

OUTPUT_DIR = Path(
    "artifacts/rank_baseline/comparisons"
)


class RankComparisonBuilder:

    def build(
        self,
        lower_rank,
        higher_rank,
    ):

        lower_rank = (
            lower_rank.upper()
        )

        higher_rank = (
            higher_rank.upper()
        )

        lower_path = (
            STATISTICS_DIR
            / f"{lower_rank}_role_statistics.csv"
        )

        higher_path = (
            STATISTICS_DIR
            / f"{higher_rank}_role_statistics.csv"
        )

        if not lower_path.exists():

            raise FileNotFoundError(
                f"Missing statistics: "
                f"{lower_path}"
            )

        if not higher_path.exists():

            raise FileNotFoundError(
                f"Missing statistics: "
                f"{higher_path}"
            )

        lower = pd.read_csv(
            lower_path
        )

        higher = pd.read_csv(
            higher_path
        )

        # ----------------------------------
        # Rename baseline columns
        # ----------------------------------

        lower = lower.rename(
            columns={
                "sample_count":
                    "lower_sample_count",

                "confidence":
                    "lower_confidence",

                "mean":
                    "lower_mean",

                "std":
                    "lower_std",

                "p10":
                    "lower_p10",

                "p25":
                    "lower_p25",

                "p50":
                    "lower_p50",

                "p75":
                    "lower_p75",

                "p90":
                    "lower_p90",

                "max":
                    "lower_max",
            }
        )

        higher = higher.rename(
            columns={
                "sample_count":
                    "higher_sample_count",

                "confidence":
                    "higher_confidence",

                "mean":
                    "higher_mean",

                "std":
                    "higher_std",

                "p10":
                    "higher_p10",

                "p25":
                    "higher_p25",

                "p50":
                    "higher_p50",

                "p75":
                    "higher_p75",

                "p90":
                    "higher_p90",

                "max":
                    "higher_max",
            }
        )

        # ----------------------------------
        # Only join same ROLE + METRIC
        # ----------------------------------

        comparison = lower.merge(
            higher,
            on=[
                "role",
                "metric",
            ],
            how="inner",
            suffixes=(
                "_lower",
                "_higher",
            ),
        )

        comparison[
            "lower_rank"
        ] = lower_rank

        comparison[
            "higher_rank"
        ] = higher_rank

        # ----------------------------------
        # Median difference
        # ----------------------------------

        comparison[
            "median_difference"
        ] = (
            comparison[
                "higher_p50"
            ]
            -
            comparison[
                "lower_p50"
            ]
        )

        # ----------------------------------
        # Relative difference
        # ----------------------------------

        comparison[
            "median_percent_change"
        ] = (
            comparison[
                "median_difference"
            ]
            /
            comparison[
                "lower_p50"
            ]
            .replace(
                0,
                pd.NA,
            )
            * 100
        )

        # ----------------------------------
        # P75 comparison
        # ----------------------------------

        comparison[
            "p75_difference"
        ] = (
            comparison[
                "higher_p75"
            ]
            -
            comparison[
                "lower_p75"
            ]
        )

        # ----------------------------------
        # Conservative confidence
        #
        # Comparison is only as reliable as
        # the weaker of the two samples.
        # ----------------------------------

        confidence_order = {
            "VERY_LOW": 0,
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
        }

        reverse_confidence = {
            value: key
            for key, value
            in confidence_order.items()
        }

        def comparison_confidence(
            row,
        ):

            lower_score = (
                confidence_order.get(
                    row[
                        "lower_confidence"
                    ],
                    0,
                )
            )

            higher_score = (
                confidence_order.get(
                    row[
                        "higher_confidence"
                    ],
                    0,
                )
            )

            return (
                reverse_confidence[
                    min(
                        lower_score,
                        higher_score,
                    )
                ]
            )

        comparison[
            "comparison_confidence"
        ] = comparison.apply(
            comparison_confidence,
            axis=1,
        )

        # ----------------------------------
        # Output
        # ----------------------------------

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            OUTPUT_DIR
            / (
                f"{lower_rank}_to_"
                f"{higher_rank}.csv"
            )
        )

        comparison.to_csv(
            output_path,
            index=False,
        )

        # ==================================
        # REPORT
        # ==================================

        print()
        print(
            f"{lower_rank} -> "
            f"{higher_rank} COMPARISON"
        )

        print(
            "=" * 45
        )

        print(
            f"Comparison rows: "
            f"{len(comparison)}"
        )

        print()

        interesting_metrics = {
            "cs_at_10",
            "gold_at_10",
            "xp_at_10",
            "cs_per_min",
            "gold_per_min",
            "deaths",
            "kda",
        }

        preview = comparison[
            comparison[
                "metric"
            ].isin(
                interesting_metrics
            )
        ].copy()

        print(
            preview[
                [
                    "role",
                    "metric",

                    "lower_sample_count",
                    "higher_sample_count",

                    "lower_p50",
                    "higher_p50",

                    "median_difference",
                    "median_percent_change",

                    "comparison_confidence",
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

        return comparison