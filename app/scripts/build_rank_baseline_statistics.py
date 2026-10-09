from app.ml.rank_baseline_statistics_builder import (
    RankBaselineStatisticsBuilder,
)


TIER = "DIAMOND"


def main():

    builder = (
        RankBaselineStatisticsBuilder()
    )

    builder.build(
        tier=TIER
    )


if __name__ == "__main__":
    main()