
from collections import defaultdict
from statistics import median
from math import isfinite


class EconomicDisruptionDetector:
    DETECTOR_ID = "ECON_002"

    BASELINE_WINDOW = 3

    MIN_INTERVAL_SECONDS = 30
    MAX_INTERVAL_SECONDS = 120

    MIN_GOLD_BASELINE_PER_MIN = 250
    MIN_XP_BASELINE_PER_MIN = 300

    MIN_GOLD_DROP_PER_MIN = 100
    MIN_RELATIVE_DROP = 0.25

    RECOVERY_THRESHOLD = 0.80
    RECOVERY_WINDOW = 3
    MIN_RECOVERY_OBSERVATIONS = 2

    MAX_GAP_MINUTES = 2.0
    EPISODE_GAP_MINUTES = 1.25

    MAX_LEVEL = 18

    EVENT_FIELDS = (
        "kills",
        "deaths",
        "assists",
        "objectives",
        "dragons",
        "buildings",
        "plates",
    )

    METRICS = {
        "gold": {
            "minimum_baseline": MIN_GOLD_BASELINE_PER_MIN,
            "minimum_absolute_drop": MIN_GOLD_DROP_PER_MIN,
        },
        "xp": {
            "minimum_baseline": MIN_XP_BASELINE_PER_MIN,
            "minimum_absolute_drop": 0,
        },
    }

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
            records.sort(
                key=lambda x: (
                    self._number(x.get("start_minute"))
                    if self._number(x.get("start_minute")) is not None
                    else float("inf")
                )
            )

            candidates = self._detect_match_candidates(records)

            match_results.append({
                "detector_id": self.DETECTOR_ID,
                "match_id": match_id,
                "participant_id": participant_id,
                "champion": records[0].get("champion"),
                "role": records[0].get("role"),
                "candidate_count": len(candidates),
                "candidates": candidates,
            })

        all_candidates = [
            candidate
            for match in match_results
            for candidate in match["candidates"]
        ]

        return {
            "detector_id": self.DETECTOR_ID,
            "matches_analyzed": len(match_results),
            "total_candidates": len(all_candidates),
            "metric_summary": self._metric_summary(all_candidates),
            "match_results": match_results,
        }

    def _detect_match_candidates(self, records):
        raw_candidates = []

        for index, current in enumerate(records):
            if index < self.BASELINE_WINDOW:
                continue

            previous = records[
                index - self.BASELINE_WINDOW:index
            ]

            if not self._is_eligible(current):
                continue

            if not all(self._is_eligible(item) for item in previous):
                continue

            if not self._are_consecutive(previous, current):
                continue

            for metric, config in self.METRICS.items():
                candidate = self._evaluate_metric(
                    metric=metric,
                    config=config,
                    previous=previous,
                    current=current,
                )

                if candidate is not None:
                    raw_candidates.append(candidate)

        episodes = self._group_candidates(raw_candidates)

        for episode in episodes:
            recovery = self._evaluate_episode_recovery(
                episode=episode,
                records=records,
                raw_candidates=raw_candidates,
            )

            episode["recovery"] = recovery

        return episodes

    def _evaluate_metric(
        self,
        metric,
        config,
        previous,
        current,
    ):
        baseline_rates = [
            self._rate(item, metric)
            for item in previous
        ]

        if any(rate is None for rate in baseline_rates):
            return None

        baseline = median(baseline_rates)
        observed = self._rate(current, metric)

        if observed is None or baseline <= 0:
            return None

        absolute_drop = baseline - observed
        relative_drop = absolute_drop / baseline

        if baseline < config["minimum_baseline"]:
            return None

        if absolute_drop < config["minimum_absolute_drop"]:
            return None

        if relative_drop < self.MIN_RELATIVE_DROP:
            return None

        return {
            "detector_id": self.DETECTOR_ID,
            "metric": metric,
            "start_minute": current.get("start_minute"),
            "end_minute": current.get("end_minute"),
            "baseline_per_min": round(baseline, 2),
            "observed_per_min": round(observed, 2),
            "absolute_drop_per_min": round(absolute_drop, 2),
            "relative_drop_percent": round(
                relative_drop * 100, 2
            ),
            "event_context": self._normalize_events(
                current.get("events")
            ),
            "confidence": "low",
            "interpretation": (
                "Economic rate deviation associated with this "
                "interval. Event association does not establish "
                "causation."
            ),
        }

    def _group_candidates(self, candidates):
        grouped = defaultdict(list)

        for candidate in candidates:
            grouped[candidate["metric"]].append(candidate)

        episodes = []

        for metric, metric_candidates in grouped.items():
            metric_candidates.sort(
                key=lambda x: x["start_minute"]
            )

            current_episode = []

            for candidate in metric_candidates:
                if not current_episode:
                    current_episode = [candidate]
                    continue

                previous = current_episode[-1]

                gap = (
                    candidate["start_minute"]
                    - previous["end_minute"]
                )

                if (
                    gap <= self.EPISODE_GAP_MINUTES
                    and gap >= -0.05
                ):
                    current_episode.append(candidate)
                else:
                    episodes.append(
                        self._build_episode(
                            metric,
                            current_episode,
                        )
                    )
                    current_episode = [candidate]

            if current_episode:
                episodes.append(
                    self._build_episode(
                        metric,
                        current_episode,
                    )
                )

        episodes.sort(
            key=lambda x: (
                x["start_minute"],
                x["metric"],
            )
        )

        return episodes

    def _build_episode(self, metric, candidates):
        baselines = [
            item["baseline_per_min"]
            for item in candidates
        ]

        observations = [
            item["observed_per_min"]
            for item in candidates
        ]

        baseline = median(baselines)
        minimum_observed = min(observations)

        absolute_drop = baseline - minimum_observed

        relative_drop = (
            absolute_drop / baseline
            if baseline > 0
            else 0
        )

        event_context = {
            field: sum(
                item["event_context"].get(field, 0)
                for item in candidates
            )
            for field in self.EVENT_FIELDS
        }

        return {
            "detector_id": self.DETECTOR_ID,
            "metric": metric,
            "episode_id": (
                f"{metric}_{candidates[0]['start_minute']:.2f}"
            ),
            "start_minute": candidates[0]["start_minute"],
            "end_minute": candidates[-1]["end_minute"],
            "duration_minutes": round(
                candidates[-1]["end_minute"]
                - candidates[0]["start_minute"],
                2,
            ),
            "interval_count": len(candidates),
            "baseline_per_min": round(baseline, 2),
            "observed_per_min": round(minimum_observed, 2),
            "absolute_drop_per_min": round(absolute_drop, 2),
            "relative_drop_percent": round(
                relative_drop * 100,
                2,
            ),
            "event_context": event_context,
            "intervals": [
                {
                    "start_minute": item["start_minute"],
                    "end_minute": item["end_minute"],
                    "baseline_per_min": item["baseline_per_min"],
                    "observed_per_min": item["observed_per_min"],
                    "relative_drop_percent": (
                        item["relative_drop_percent"]
                    ),
                }
                for item in candidates
            ],
            "recovery": {
                "status": "pending",
                "observed_per_min": None,
            },
            "confidence": "low",
            "interpretation": (
                "A sustained deviation from the local economic "
                "baseline was detected. Nearby events are contextual "
                "evidence, not proof of cause."
            ),
            "limitations": [
                "Small personal baseline",
                "Economic changes may reflect intentional map activity",
                "No opponent or game-state adjustment",
                "Episode grouping is based on temporal proximity",
                "Recovery uses a short observation window",
            ],
        }

    def _evaluate_episode_recovery(
        self,
        episode,
        records,
        raw_candidates,
    ):
        metric = episode["metric"]
        episode_end = episode["end_minute"]
        baseline = episode["baseline_per_min"]

        candidate_starts = {
            (
                item["metric"],
                item["start_minute"],
            )
            for item in raw_candidates
        }

        recovery_intervals = []

        for interval in records:
            start = self._number(
                interval.get("start_minute")
            )
            end = self._number(
                interval.get("end_minute")
            )

            if start is None or end is None:
                continue

            if start < episode_end - 0.05:
                continue

            if (
                metric,
                start,
            ) in candidate_starts:
                continue

            if not self._is_metric_eligible(interval, metric):
                continue

            rate = self._rate(interval, metric)

            if rate is None:
                continue

            recovery_intervals.append({
                "start_minute": start,
                "end_minute": end,
                "rate": rate,
            })

            if len(recovery_intervals) >= self.RECOVERY_WINDOW:
                break

        rates = [
            item["rate"]
            for item in recovery_intervals
        ]

        if len(rates) < self.MIN_RECOVERY_OBSERVATIONS:
            return {
                "status": "unavailable",
                "observed_per_min": (
                    round(median(rates), 2)
                    if rates
                    else None
                ),
                "observations": len(rates),
                "required_observations": (
                    self.MIN_RECOVERY_OBSERVATIONS
                ),
            }

        recovery_rate = median(rates)
        threshold = baseline * self.RECOVERY_THRESHOLD

        return {
            "status": (
                "recovered"
                if recovery_rate >= threshold
                else "not_recovered"
            ),
            "observed_per_min": round(recovery_rate, 2),
            "recovery_threshold_per_min": round(threshold, 2),
            "observations": len(rates),
            "window": [
                {
                    "start_minute": item["start_minute"],
                    "end_minute": item["end_minute"],
                    "rate_per_min": round(item["rate"], 2),
                }
                for item in recovery_intervals
            ],
        }

    def _is_metric_eligible(self, interval, metric):
        if not self._is_eligible(interval):
            return False

        if metric == "xp":
            level_start = self._number(
                interval.get("level_start")
            )

            if (
                level_start is not None
                and level_start >= self.MAX_LEVEL
            ):
                return False

        return self._rate(interval, metric) is not None

    def _is_eligible(self, interval):
        duration = self._number(
            interval.get("elapsed_seconds")
        )

        if duration is None:
            return False

        return (
            self.MIN_INTERVAL_SECONDS
            <= duration
            <= self.MAX_INTERVAL_SECONDS
        )

    def _are_consecutive(self, previous, current):
        sequence = previous + [current]

        for first, second in zip(sequence, sequence[1:]):
            first_end = self._number(
                first.get("end_minute")
            )
            second_start = self._number(
                second.get("start_minute")
            )

            if first_end is None or second_start is None:
                return False

            gap = second_start - first_end

            if gap < -0.05 or gap > self.MAX_GAP_MINUTES:
                return False

        return True

    def _rate(self, interval, metric):
        if metric == "xp":
            level_start = self._number(
                interval.get("level_start")
            )

            if (
                level_start is not None
                and level_start >= self.MAX_LEVEL
            ):
                return None

        delta = self._number(
            interval.get(f"{metric}_delta")
        )

        duration = self._number(
            interval.get("elapsed_seconds")
        )

        if delta is None or duration is None:
            return None

        if delta < 0 or duration <= 0:
            return None

        return delta / (duration / 60)

    @classmethod
    def _normalize_events(cls, events):
        events = events or {}

        return {
            field: events.get(field, 0)
            for field in cls.EVENT_FIELDS
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

    def _metric_summary(self, candidates):
        summary = {}

        for metric in self.METRICS:
            metric_candidates = [
                candidate
                for candidate in candidates
                if candidate["metric"] == metric
            ]

            summary[metric] = {
                "episode_count": len(metric_candidates),
                "recovered": sum(
                    1
                    for item in metric_candidates
                    if item["recovery"]["status"] == "recovered"
                ),
                "not_recovered": sum(
                    1
                    for item in metric_candidates
                    if item["recovery"]["status"] == "not_recovered"
                ),
                "recovery_unavailable": sum(
                    1
                    for item in metric_candidates
                    if item["recovery"]["status"] == "unavailable"
                ),
            }

        return summary
