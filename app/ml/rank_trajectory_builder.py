from pathlib import Path

import pandas as pd


STATISTICS_DIR = Path(
    "artifacts/rank_baseline/statistics"
)

OUTPUT_DIR = Path(
    "artifacts/rank_baseline/trajectories"
)


class RankTrajectoryBuilder:

    RANKS = [
        "GOLD",
        "PLATINUM",
        "EMERALD",
        "DIAMOND",
    ]

    RANK_ORDER = {
        "GOLD": 0,
        "PLATINUM": 1,
        "EMERALD": 2,
        "DIAMOND": 3,
    }

    def _load_rank(
        self,
        rank,
    ):

        path = (
            STATISTICS_DIR
            / f"{rank}_role_statistics.csv"
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Missing statistics file: {path}"
            )

        df = pd.read_csv(
            path
        )

        df["rank"] = rank

        df["rank_order"] = (
            self.RANK_ORDER[
                rank
            ]
        )

        return df

    @staticmethod
    def _direction_changes(
        values,
    ):

        changes = 0

        previous_direction = None

        for i in range(
            1,
            len(values),
        ):

            difference = (
                values[i]
                - values[i - 1]
            )

            if difference == 0:
                continue

            direction = (
                1
                if difference > 0
                else -1
            )

            if (
                previous_direction
                is not None
                and
                direction
                != previous_direction
            ):

                changes += 1

            previous_direction = (
                direction
            )

        return changes

    @staticmethod
    def _monotonicity_score(
        values,
    ):

        if len(values) < 2:
            return 0.0

        increasing = 0
        decreasing = 0

        total_steps = (
            len(values)
            - 1
        )

        for i in range(
            1,
            len(values),
        ):

            diff = (
                values[i]
                - values[i - 1]
            )

            if diff > 0:
                increasing += 1

            elif diff < 0:
                decreasing += 1

        strongest_direction = max(
            increasing,
            decreasing,
        )

        return (
            strongest_direction
            / total_steps
        )

    @staticmethod
    def _trend_direction(
        first_value,
        last_value,
    ):

        if last_value > first_value:
            return "INCREASING"

        if last_value < first_value:
            return "DECREASING"

        return "FLAT"

    @staticmethod
    def _minimum_confidence(
        confidences,
    ):

        order = {
            "VERY_LOW": 0,
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
        }

        reverse = {
            value: key
            for key, value
            in order.items()
        }

        minimum = min(
            order.get(
                value,
                0,
            )
            for value
            in confidences
        )

        return reverse[
            minimum
        ]

    def build(
        self,
    ):

        frames = []

        for rank in self.RANKS:

            frames.append(
                self._load_rank(
                    rank
                )
            )

        all_stats = pd.concat(
            frames,
            ignore_index=True,
        )

        rows = []

        grouped = (
            all_stats
            .groupby(
                [
                    "role",
                    "metric",
                ]
            )
        )

        for (
            role,
            metric,
        ), group in grouped:

            group = (
                group
                .sort_values(
                    "rank_order"
                )
            )

            if (
                len(group)
                != len(
                    self.RANKS
                )
            ):
                continue

            medians = (
                group[
                    "p50"
                ]
                .astype(float)
                .tolist()
            )

            confidences = (
                group[
                    "confidence"
                ]
                .tolist()
            )

            sample_counts = (
                group[
                    "sample_count"
                ]
                .astype(int)
                .tolist()
            )

            first_value = (
                medians[0]
            )

            last_value = (
                medians[-1]
            )

            absolute_change = (
                last_value
                - first_value
            )

            percent_change = None

            if first_value != 0:

                percent_change = (
                    absolute_change
                    / first_value
                    * 100
                )

            monotonicity = (
                self._monotonicity_score(
                    medians
                )
            )

            direction_changes = (
                self._direction_changes(
                    medians
                )
            )

            rows.append({
                "role":
                    role,

                "metric":
                    metric,

                "gold_p50":
                    medians[0],

                "platinum_p50":
                    medians[1],

                "emerald_p50":
                    medians[2],

                "diamond_p50":
                    medians[3],

                "gold_n":
                    sample_counts[0],

                "platinum_n":
                    sample_counts[1],

                "emerald_n":
                    sample_counts[2],

                "diamond_n":
                    sample_counts[3],

                "overall_direction":
                    self._trend_direction(
                        first_value,
                        last_value,
                    ),

                "absolute_change":
                    absolute_change,

                "percent_change":
                    percent_change,

                "monotonicity_score":
                    monotonicity,

                "direction_changes":
                    direction_changes,

                "trajectory_confidence":
                    self._minimum_confidence(
                        confidences
                    ),
            })

        result = pd.DataFrame(
            rows
        )

        if not result.empty:

            result[
                "trend_strength"
            ] = (
                result[
                    "percent_change"
                ]
                .abs()
                *
                result[
                    "monotonicity_score"
                ]
            )

            result = (
                result
                .sort_values(
                    [
                        "role",
                        "trend_strength",
                    ],
                    ascending=[
                        True,
                        False,
                    ],
                )
            )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            OUTPUT_DIR
            / "GOLD_to_DIAMOND_trajectories.csv"
        )

        result.to_csv(
            output_path,
            index=False,
        )

        print()
        print(
            "GOLD -> DIAMOND "
            "RANK TRAJECTORIES"
        )

        print(
            "=" * 55
        )

        print(
            f"Trajectory rows: "
            f"{len(result)}"
        )

        if not result.empty:

            interesting = {
                "cs_at_10",
                "gold_at_10",
                "xp_at_10",
                "cs_per_min",
                "gold_per_min",
                "deaths",
                "kda",
            }

            preview = result[
                result[
                    "metric"
                ].isin(
                    interesting
                )
            ]

            print()
            print(
                preview[
                    [
                        "role",
                        "metric",

                        "gold_p50",
                        "platinum_p50",
                        "emerald_p50",
                        "diamond_p50",

                        "percent_change",
                        "monotonicity_score",
                        "direction_changes",

                        "trajectory_confidence",
                    ]
                ]
                .to_string(
                    index=False
                )
            )

        print()
        print(
            f"Saved: {output_path}"
        )

        return result