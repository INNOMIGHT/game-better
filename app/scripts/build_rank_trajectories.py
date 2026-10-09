from app.ml.rank_trajectory_builder import (
    RankTrajectoryBuilder,
)


def main():

    builder = (
        RankTrajectoryBuilder()
    )

    builder.build()


if __name__ == "__main__":
    main()