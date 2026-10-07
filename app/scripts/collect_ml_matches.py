from app.database.database import SessionLocal
from app.services.ml_match_collection_service import (
    MLMatchCollectionService,
)


RIOT_ACCOUNT_ID = 1
PLATFORM = "EUW1"

TARGET_NEW_MATCHES = 200
MATCHES_PER_PLAYER = 20
MAX_PLAYERS = 100


def main():

    db = SessionLocal()

    try:

        service = MLMatchCollectionService(db)

        result = service.collect_from_account(
            riot_account_id=RIOT_ACCOUNT_ID,
            platform=PLATFORM,
            target_new_matches=TARGET_NEW_MATCHES,
            matches_per_player=MATCHES_PER_PLAYER,
            max_players=MAX_PLAYERS,
        )

        print()
        print()
        print("ML MATCH COLLECTION COMPLETE")
        print("============================")

        for key, value in result.items():

            if key in {
                "failed_matches",
                "failed_players",
            }:
                continue

            print(
                f"{key}: {value}"
            )

        if result["failed_players"]:

            print()
            print("FAILED PLAYERS")
            print("==============")

            for failure in result[
                "failed_players"
            ]:
                print(failure)

        if result["failed_matches"]:

            print()
            print("FAILED MATCHES")
            print("==============")

            for failure in result[
                "failed_matches"
            ]:
                print(failure)

    finally:

        db.close()


if __name__ == "__main__":
    main()