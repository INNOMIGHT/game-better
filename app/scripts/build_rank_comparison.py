from app.ml.rank_comparison_builder import (
    RankComparisonBuilder,
)

LOWER_RANK = "EMERALD"
HIGHER_RANK = "DIAMOND"


def main():

    builder = (
        RankComparisonBuilder()
    )

    builder.build(
        lower_rank=
            LOWER_RANK,

        higher_rank=
            HIGHER_RANK,
    )


if __name__ == "__main__":

    main()