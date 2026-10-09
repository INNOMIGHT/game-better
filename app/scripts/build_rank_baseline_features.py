from app.database.database import (
    SessionLocal,
)

from app.ml.participant_baseline_feature_builder import (
    ParticipantBaselineFeatureBuilder,
)


TIER = "DIAMOND"


def main():

    db = SessionLocal()

    try:

        builder = (
            ParticipantBaselineFeatureBuilder(
                db
            )
        )

        builder.build(
            tier=TIER
        )

    finally:

        db.close()


if __name__ == "__main__":

    main()