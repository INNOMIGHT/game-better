from app.database.database import SessionLocal
from app.services.contextual_farming_service import (
    ContextualFarmingService,
)
from app.services.farming_disruption_detector import (
FarmingDisruptionDetector,
)


from app.services.death_pattern_detector import (
DeathPatternDetector,
)

from app.services.economy_efficiency_detector import (
    EconomyEfficiencyDetector,
)

from app.services.economic_disruption_detector import (
    EconomicDisruptionDetector,
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


    death_detector = DeathPatternDetector()

    death_results = death_detector.detect(result["intervals"])

    print("\n========== DEATH_001 ==========")

    print(
        "Matches analyzed:",
        death_results["matches_analyzed"],
    )

    print("\nRole summary:")

    for role, summary in death_results["role_summary"].items():
        print(f"\nRole: {role}")
        print("Matches:", summary["matches_analyzed"])

        for phase, stats in summary["phases"].items():
            print(
                phase,
                "| deaths:", stats["deaths"],
                "| minutes:", stats["minutes_observed"],
                "| deaths/10 min:", stats["deaths_per_10_minutes"],
            )

    print("\nPer-match details:")

    for match in death_results["match_results"]:
        print(
            match["match_id"],
            match["champion"],
            match["role"],
            match["phases"],
        )


        # ECON_001: Economy Efficiency
    economy_detector = EconomyEfficiencyDetector()

    economy_results = economy_detector.detect(
        result["intervals"]
    )

    print("\n========== ECON_001 ==========")

    print(
        "Matches analyzed:",
        economy_results["matches_analyzed"]
    )

    print("\nRole Summary:")

    for role, summary in economy_results["role_summary"].items():
        print(f"\nRole: {role}")
        print(f"Matches: {summary['matches']}")

        for phase_name, phase in summary["phases"].items():
            print(f"\n  {phase_name.upper()}")

            print(
                f"    Gold/min: {phase['gold_per_min']}"
            )

            print(
                f"    XP/min: {phase['xp_per_min']}"
            )

            print(
                f"    CS/min: {phase['cs_per_min']}"
            )

            print(
                f"    Valid intervals: "
                f"Gold={phase['gold_valid_intervals']}, "
                f"XP={phase['xp_valid_intervals']}, "
                f"CS={phase['cs_valid_intervals']}"
            )

    print("\nPer Match:")

    for match in economy_results["match_results"]:
        print(
            f"\n{match['champion']} | "
            f"{match['role']} | {match['match_id']}"
        )

        for phase_name, phase in match["phases"].items():
            print(
                f"  {phase_name}: "
                f"Gold/min={phase['gold_per_min']}, "
                f"XP/min={phase['xp_per_min']}, "
                f"CS/min={phase['cs_per_min']}"
            )

    # ECON_002: Economic Disruption and Recovery

    disruption_detector = EconomicDisruptionDetector()

    disruption_results = disruption_detector.detect(
        result["intervals"]
    )

    print("\n========== ECON_002 ==========")

    print(
        "Matches analyzed:",
        disruption_results["matches_analyzed"]
    )

    print(
        "Total candidates:",
        disruption_results["total_candidates"]
    )

    print("\nMetric Summary:")

    for metric, summary in disruption_results["metric_summary"].items():
        print(f"\n{metric.upper()}")

        for key, value in summary.items():
            print(f"  {key}: {value}")

    print("\nPer Match:")

    for match in disruption_results["match_results"]:
        print(
            f"\n{match['champion']} | "
            f"{match['role']} | {match['match_id']}"
        )

        print(
            "Candidates:",
            match["candidate_count"]
        )

        for candidate in match["candidates"]:
            print(
                f"  {candidate['metric'].upper()} | "
                f"{candidate['start_minute']:.2f}-"
                f"{candidate['end_minute']:.2f} min"
            )

            print(
                f"    Baseline: "
                f"{candidate['baseline_per_min']}"
            )

            print(
                f"    Observed: "
                f"{candidate['observed_per_min']}"
            )

            print(
                f"    Drop: "
                f"{candidate['relative_drop_percent']}%"
            )

            print(
                f"    Events: "
                f"{candidate['event_context']}"
            )

            print(
                f"    Recovery: "
                f"{candidate['recovery']}"
            )


finally:
    db.close()

