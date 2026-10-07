from app.database.database import (
    SessionLocal,
)

from app.ml.farm_recovery_dataset_builder import (
    build_farm_recovery_dataset,
)


def main():

    db = SessionLocal()

    try:

        df = (
            build_farm_recovery_dataset(
                db
            )
        )

        print()
        print("Sample:")
        print(
            df.head(
                10
            ).to_string(
                index=False
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()