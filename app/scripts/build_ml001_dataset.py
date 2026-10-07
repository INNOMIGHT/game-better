
from app.database.database import SessionLocal
from app.ml.dataset_builder import build_dataset


def main():
    db = SessionLocal()

    try:
        df, report = build_dataset(db)

        print("\nML_001 DATASET REPORT")
        print("=====================")

        for key, value in report.items():
            print(f"{key}: {value}")

        print("\nSample rows:")
        print(
            df.head(10).to_string(index=False)
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
