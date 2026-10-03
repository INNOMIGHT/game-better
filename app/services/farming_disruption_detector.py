
from collections import defaultdict
from statistics import median
from math import isfinite


class FarmingDisruptionDetector:
    """
    Experimental detector for sudden farming-rate declines.

    Input: normalized interval dictionaries from
    ContextualFarmingService.

    Output: diagnostic candidates only.
    No database writes or player-facing conclusions.
    """

    BASELINE_INTERVALS = 3
    MIN_BASELINE_CSPM = 4.0
    MIN_ABSOLUTE_DROP = 2.0
    MIN_PERCENT_DROP = 30.0
    RECOVERY_THRESHOLD = 0.80

    def detect(self, intervals: list[dict]) -> list[dict]:
        grouped = defaultdict(list)

        for interval in intervals:
            key = (
                interval.get("match_id"),
                interval.get("participant_id"),
            )
            grouped[key].append(interval)

        findings = []

        for (match_id, participant_id), records in grouped.items():
            records.sort(key=lambda x: x["start_minute"])

            eligible = [
                record for record in records
                if self._is_eligible(record)
            ]

            for index in range(self.BASELINE_INTERVALS, len(eligible)):
                current = eligible[index]

                previous = eligible[
                    index - self.BASELINE_INTERVALS:index
                ]

                baseline = median(
                    item["cs_per_minute"] for item in previous
                )

                observed = current["cs_per_minute"]

                if baseline < self.MIN_BASELINE_CSPM:
                    continue

                absolute_drop = baseline - observed
                percent_drop = (absolute_drop / baseline) * 100

                if (
                    absolute_drop < self.MIN_ABSOLUTE_DROP
                    or percent_drop < self.MIN_PERCENT_DROP
                ):
                    continue

                next_interval = (
                    eligible[index + 1]
                    if index + 1 < len(eligible)
                    else None
                )

                recovery = None

                if next_interval is not None:
                    recovery = (
                        next_interval["cs_per_minute"]
                        >= baseline * self.RECOVERY_THRESHOLD
                    )

                events = current.get("events") or {}

                findings.append({
                    "detector_id": "FARM_002",
                    "finding_type": "farming_disruption_candidate",
                    "match_id": match_id,
                    "participant_id": participant_id,
                    "champion": current.get("champion"),
                    "role": current.get("role"),
                    "start_minute": current["start_minute"],
                    "end_minute": current["end_minute"],
                    "baseline_cs_per_min": round(baseline, 2),
                    "observed_cs_per_min": round(observed, 2),
                    "absolute_drop": round(absolute_drop, 2),
                    "percentage_drop": round(percent_drop, 2),
                    "event_context": {
                        "kills": events.get("kills", 0),
                        "deaths": events.get("deaths", 0),
                        "assists": events.get("assists", 0),
                        "objectives": events.get("objectives", 0),
                    },
                    "recovered_next_interval": recovery,
                    "confidence": "low",
                    "interpretation": (
                        "A farming-rate decline was detected. "
                        "The available signals do not establish its cause."
                    ),
                })

        return findings

    @staticmethod
    def _is_eligible(interval: dict) -> bool:
        value = interval.get("cs_per_minute")

        if value is None:
            return False

        try:
            value = float(value)
        except (TypeError, ValueError):
            return False

        return (
            isfinite(value)
            and value >= 0
            and interval.get("cs_delta") is not None
            and interval.get("end_minute", 0) >= 2
        )