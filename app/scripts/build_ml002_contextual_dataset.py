from app.database.database import (
    SessionLocal,
)

from app.ml.contextual_dataset_builder import (
    build_contextual_dataset,
)


def main():

    db = SessionLocal()

    try:

        df = build_contextual_dataset(
            db
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