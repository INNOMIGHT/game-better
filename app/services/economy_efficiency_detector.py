
from collections import defaultdict
from math import isfinite


class EconomyEfficiencyDetector:
    EARLY_END = 14.0
    MID_END = 25.0

    METRICS = ("gold", "xp", "cs")

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

                duration = self._number(
                    interval.get("elapsed_seconds")
                )

                if duration is None or duration <= 0:
                    continue

                phase_record = phase_data[phase]
                phase_record["intervals"] += 1

                for metric in self.METRICS:
                    value = self._number(
                        interval.get(f"{metric}_delta")
                    )

                    if value is None or value < 0:
                        continue

                    phase_record[f"{metric}_total"] += value
                    phase_record[f"{metric}_duration_seconds"] += duration
                    phase_record[f"{metric}_valid_intervals"] += 1

            for phase in phase_data.values():
                self._calculate_rates(phase)

            match_results.append({
                "detector_id": "ECON_001",
                "match_id": match_id,
                "participant_id": participant_id,
                "champion": records[0].get("champion"),
                "role": records[0].get("role"),
                "phases": phase_data,
            })

        return {
            "detector_id": "ECON_001",
            "matches_analyzed": len(match_results),
            "match_results": match_results,
            "role_summary": self._aggregate_by_role(match_results),
        }

    @staticmethod
    def _number(value):
        if isinstance(value, bool):
            return None

        if not isinstance(value, (int, float)):
            return None

        value = float(value)

        if not isfinite(value):
            return None

        return value

    def _get_phase(self, interval):
        start = self._number(interval.get("start_minute"))
        end = self._number(interval.get("end_minute"))

        if start is None or end is None or end < start:
            return None

        midpoint = (start + end) / 2

        if midpoint < self.EARLY_END:
            return "early"

        if midpoint < self.MID_END:
            return "mid"

        return "late"

    @staticmethod
    def _empty_phase():
        phase = {
            "intervals": 0,
        }

        for metric in ("gold", "xp", "cs"):
            phase[f"{metric}_total"] = 0.0
            phase[f"{metric}_duration_seconds"] = 0.0
            phase[f"{metric}_valid_intervals"] = 0
            phase[f"{metric}_per_min"] = None

        return phase

    @staticmethod
    def _calculate_rates(phase):
        for metric in ("gold", "xp", "cs"):
            total = phase[f"{metric}_total"]
            seconds = phase[f"{metric}_duration_seconds"]

            if seconds > 0:
                rate = total / (seconds / 60)
                phase[f"{metric}_per_min"] = round(rate, 2)

            phase[f"{metric}_total"] = round(total, 2)
            phase[f"{metric}_duration_seconds"] = round(seconds, 2)

    def _aggregate_by_role(self, match_results):
        grouped = defaultdict(list)

        for result in match_results:
            role = result.get("role") or "UNKNOWN"
            grouped[role].append(result)

        role_summary = {}

        for role, matches in grouped.items():
            role_phases = {
                "early": self._empty_phase(),
                "mid": self._empty_phase(),
                "late": self._empty_phase(),
            }

            for match in matches:
                for phase_name, phase in match["phases"].items():
                    target = role_phases[phase_name]

                    target["intervals"] += phase["intervals"]

                    for metric in self.METRICS:
                        target[f"{metric}_total"] += phase[
                            f"{metric}_total"
                        ]

                        target[f"{metric}_duration_seconds"] += phase[
                            f"{metric}_duration_seconds"
                        ]

                        target[f"{metric}_valid_intervals"] += phase[
                            f"{metric}_valid_intervals"
                        ]

            for phase in role_phases.values():
                self._calculate_rates(phase)

            role_summary[role] = {
                "matches": len(matches),
                "phases": role_phases,
            }

        return role_summary