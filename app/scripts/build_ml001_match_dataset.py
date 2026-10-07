from app.database.database import SessionLocal
from app.ml.match_dataset_builder import (
    build_match_dataset,
)


def main():

    db = SessionLocal()

    try:

        df, report = (
            build_match_dataset(db)
        )

        print()
        print(
            "ML_001 MATCH DATASET REPORT"
        )

        print(
            "==========================="
        )

        for key, value in report.items():
            print(
                f"{key}: {value}"
            )

        print()
        print("Sample:")
        print(
            df.head().to_string(
                index=False
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()