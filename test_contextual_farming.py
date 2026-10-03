from app.database.database import SessionLocal
from app.services.contextual_farming_service import (
    ContextualFarmingService,
)
from app.services.farming_disruption_detector import (
FarmingDisruptionDetector,
)


RIOT_ACCOUNT_ID = 1  # Replace with your actual account ID


db = SessionLocal()

try:
    service = ContextualFarmingService(db)

    result = service.get_player_interval_features(
        riot_account_id=RIOT_ACCOUNT_ID,
        limit=10,
    )

    if result is None:
        print("Riot account not found")

    else:
        print("Matches analyzed:", result["matches_analyzed"])
        print("Total intervals:", result["total_intervals"])
        print(
            "Skipped intervals:",
            len(result["skipped_intervals"]),
        )

        print("\nFirst 10 intervals:")

        for interval in result["intervals"][:10]:
            print(interval)

        print("\n=== INTERVALS WITH PLAYER EVENTS ===")

    for interval in result["intervals"]:

        events = interval["events"]

        has_events = any(
            value > 0
            for value in events.values()
        )

        if has_events:
            print({
                "match_id": interval["match_id"],
                "champion": interval["champion"],
                "role": interval["role"],
                "interval": (
                    interval["start_minute"],
                    interval["end_minute"],
                ),
                "cs_delta": interval["cs_delta"],
                "cs_per_minute": interval["cs_per_minute"],
                "gold_delta": interval["gold_delta"],
                "events": events,
            })


    print("\n=== BRAND DEATH VALIDATION ===")

    for interval in result["intervals"]:

        if (
            interval["match_id"] == "EUW1_7954667315"
            and interval["champion"] == "Brand"
            and interval["events"]["deaths"] > 0
        ):
            print(interval)


    detector = FarmingDisruptionDetector()

    findings = detector.detect(result["intervals"])

    print(f"\nFARM_002 candidates: {len(findings)}")

    for finding in findings:
        print(finding)

finally:
    db.close()

