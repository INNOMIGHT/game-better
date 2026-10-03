
from collections import defaultdict


class DeathPatternDetector:
    """
    DEATH_001: Descriptive death-pattern analysis.

    Consumes normalized contextual farming intervals.
    Does not write to the database.
    Does not infer avoidability or causation.
    """

    EARLY_END = 14.0
    MID_END = 25.0

    def detect(self, intervals: list[dict]) -> dict:
        grouped = defaultdict(list)

        for interval in intervals:
            key = (
                interval.get("match_id"),
                interval.get("participant_id"),
            )
            grouped[key].append(interval)

        match_results = []

        for (match_id, participant_id), records in grouped.items():
            records.sort(key=lambda x: x["start_minute"])

            phase_data = {
                "early": self._empty_phase(),
                "mid": self._empty_phase(),
                "late": self._empty_phase(),
            }

            for interval in records:
                phase = self._get_phase(interval)

                if phase is None:
                    continue

                duration = interval.get("elapsed_seconds")

                if duration is None or duration <= 0:
                    continue

                events = interval.get("events") or {}
                deaths = events.get("deaths", 0)

                phase_data[phase]["duration_seconds"] += duration
                phase_data[phase]["deaths"] += deaths
                phase_data[phase]["intervals"] += 1

                if deaths > 0:
                    phase_data[phase]["death_intervals"] += 1

            for phase in phase_data.values():
                minutes = phase["duration_seconds"] / 60

                phase["minutes_observed"] = round(minutes, 2)

                phase["deaths_per_10_minutes"] = (
                    round(phase["deaths"] / minutes * 10, 2)
                    if minutes > 0
                    else None
                )

                phase["death_interval_frequency_percent"] = (
                    round(
                        phase["death_intervals"]
                        / phase["intervals"] * 100,
                        2,
                    )
                    if phase["intervals"] > 0
                    else None
                )

            match_results.append({
                "detector_id": "DEATH_001",
                "match_id": match_id,
                "participant_id": participant_id,
                "champion": records[0].get("champion"),
                "role": records[0].get("role"),
                "phases": phase_data,
                "total_deaths": sum(
                    p["deaths"] for p in phase_data.values()
                ),
            })

        return {
            "detector_id": "DEATH_001",
            "matches_analyzed": len(match_results),
            "match_results": match_results,
            "role_summary": self._aggregate_by_role(match_results),
        }

    @staticmethod
    def _empty_phase():
        return {
            "deaths": 0,
            "death_intervals": 0,
            "intervals": 0,
            "duration_seconds": 0,
            "minutes_observed": 0,
            "deaths_per_10_minutes": None,
            "death_interval_frequency_percent": None,
        }

    def _get_phase(self, interval: dict):
        start = interval.get("start_minute")
        end = interval.get("end_minute")

        if start is None or end is None:
            return None

        midpoint = (start + end) / 2

        if midpoint < self.EARLY_END:
            return "early"

        if midpoint < self.MID_END:
            return "mid"

        return "late"

    @staticmethod
    def _aggregate_by_role(match_results: list[dict]) -> dict:
        grouped = defaultdict(list)

        for result in match_results:
            role = result.get("role") or "UNKNOWN"
            grouped[role].append(result)

        summary = {}

        for role, matches in grouped.items():
            phases = {}

            for phase_name in ("early", "mid", "late"):
                total_deaths = sum(
                    match["phases"][phase_name]["deaths"]
                    for match in matches
                )

                total_minutes = sum(
                    match["phases"][phase_name]["minutes_observed"]
                    for match in matches
                )

                phases[phase_name] = {
                    "deaths": total_deaths,
                    "minutes_observed": round(total_minutes, 2),
                    "deaths_per_10_minutes": (
                        round(total_deaths / total_minutes * 10, 2)
                        if total_minutes > 0
                        else None
                    ),
                }

            summary[role] = {
                "matches_analyzed": len(matches),
                "phases": phases,
            }

        return summary