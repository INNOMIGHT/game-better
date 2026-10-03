
from collections import defaultdict

from app.schemas.recommendation import (
    CoachingOverview,
    CoachingInsight,
    CoachingRecommendation,
    RecommendationEvidence,
)

from app.services.timeline_analytics_service import TimelineAnalyticsService

from statistics import stdev


class RecommendationService:

    MIN_MATCHES = 5
    MIN_INSIGHT_MATCHES = 2
    MAX_INSIGHTS = 5
    MAX_RECOMMENDATIONS = 3

    MIN_CONSISTENCY_MATCHES = 5
    CONSISTENCY_DROP_THRESHOLD = 15.0
    MIN_PATTERN_FREQUENCY = 50.0

    FARMING_DROP_THRESHOLD = 15.0
    DEATH_RATE_DIFFERENCE_THRESHOLD = 0.75

    MIN_VARIABILITY_MATCHES = 5
    HIGH_VARIABILITY_CV_THRESHOLD = 20.0

    def __init__(self, db):
        self.db = db
        self.timeline_service = TimelineAnalyticsService(db)

    @staticmethod
    def _average(values):
        return sum(values) / len(values) if values else None

    @staticmethod
    def _confidence(match_count):
        if match_count >= 15:
            return "moderate"
        return "low"

    @staticmethod
    def _group_by_role(matches):
        groups = defaultdict(list)

        for match in matches:
            role = (match.role or "UNKNOWN").upper()
            groups[role].append(match)

        return groups

    @staticmethod
    def _phase_rate(phase):
        if phase is None:
            return None

        return phase.cs_per_minute

    @staticmethod
    def _phase_duration(phase):
        if phase is None:
            return 0

        return max(
            0,
            phase.end_minute - phase.start_minute
        )

    def _analyze_match_farming(self, role, match):
        phases = {
            "early": match.early_game,
            "mid": match.mid_game,
            "late": match.late_game,
        }

        available = {
            name: self._phase_rate(phase)
            for name, phase in phases.items()
            if phase is not None
            and self._phase_duration(phase) > 0
            and self._phase_rate(phase) is not None
        }

        if len(available) < 2:
            return None

        comparisons = []

        phase_order = ["early", "mid", "late"]

        for previous, current in zip(
            phase_order,
            phase_order[1:]
        ):
            if previous not in available or current not in available:
                continue

            previous_rate = available[previous]
            current_rate = available[current]

            if previous_rate <= 0:
                continue

            change = (
                (current_rate - previous_rate)
                / previous_rate
            ) * 100

            if change <= -self.FARMING_DROP_THRESHOLD:
                comparisons.append(
                    (
                        change,
                        previous,
                        current,
                        previous_rate,
                        current_rate,
                    )
                )

        if not comparisons:
            return None

        change, previous, current, previous_rate, current_rate = min(
            comparisons,
            key=lambda item: item[0]
        )

        return CoachingInsight(
            id=f"farming_drop_{role.lower()}_{match.match_id}",
            category="farming",
            title=f"{current.title()}-game farming decline",
            observation=(
                f"Your CS rate decreased from "
                f"{previous_rate:.2f} to {current_rate:.2f} "
                f"per minute between the {previous} and "
                f"{current} game phases in this match."
            ),
            confidence="low",
            matches_analyzed=1,
            evidence=[
                RecommendationEvidence(
                    metric=f"{previous}_cs_per_minute",
                    value=round(previous_rate, 2),
                ),
                RecommendationEvidence(
                    metric=f"{current}_cs_per_minute",
                    value=round(current_rate, 2),
                ),
                RecommendationEvidence(
                    metric="cs_rate_change_percent",
                    value=round(change, 2),
                ),
                RecommendationEvidence(
                    metric="role",
                    value=role,
                ),
            ],
        )

    def _analyze_farming(self, role, matches):
        if len(matches) < self.MIN_MATCHES:
            return None

        phase_values = {
            "early": [],
            "mid": [],
            "late": [],
        }

        for match in matches:
            for phase_name in phase_values:
                phase = getattr(match, f"{phase_name}_game")

                if (
                    phase is not None
                    and self._phase_duration(phase) > 0
                    and phase.cs_per_minute is not None
                ):
                    phase_values[phase_name].append(
                        phase.cs_per_minute
                    )

        averages = {
            phase: self._average(values)
            for phase, values in phase_values.items()
        }

        comparisons = [
            ("early", "mid"),
            ("mid", "late"),
        ]

        declines = []

        for previous, current in comparisons:
            previous_rate = averages[previous]
            current_rate = averages[current]

            if (
                previous_rate is None
                or current_rate is None
                or previous_rate <= 0
            ):
                continue

            change = (
                (current_rate - previous_rate)
                / previous_rate
            ) * 100

            if change <= -self.FARMING_DROP_THRESHOLD:
                declines.append(
                    (
                        change,
                        previous,
                        current,
                        previous_rate,
                        current_rate,
                    )
                )

        if not declines:
            return None

        change, previous, current, previous_rate, current_rate = min(
            declines,
            key=lambda item: item[0]
        )

        return CoachingRecommendation(
            id=f"farming_{role.lower()}",
            category="farming",
            title=f"{current.title()}-game farming decline",
            observation=(
                f"Across {len(matches)} {role} matches, "
                f"average CS/min decreased from "
                f"{previous_rate:.2f} to {current_rate:.2f} "
                f"between the {previous} and {current} phases."
            ),
            action=(
                "Review your replays around the phase transition. "
                "Check missed waves or jungle camps, unnecessary "
                "rotations, and whether fights interrupted farming."
            ),
            priority="medium",
            confidence=self._confidence(len(matches)),
            matches_analyzed=len(matches),
            evidence=[
                RecommendationEvidence(
                    metric=f"{previous}_cs_per_minute",
                    value=round(previous_rate, 2),
                ),
                RecommendationEvidence(
                    metric=f"{current}_cs_per_minute",
                    value=round(current_rate, 2),
                ),
                RecommendationEvidence(
                    metric="cs_rate_change_percent",
                    value=round(change, 2),
                ),
                RecommendationEvidence(
                    metric="role",
                    value=role,
                ),
            ],
        )

    def _analyze_deaths(self, role, matches):
        if len(matches) < self.MIN_MATCHES:
            return None

        phase_rates = {
            "early": [],
            "mid": [],
            "late": [],
        }

        for match in matches:
            for phase_name in phase_rates:
                phase = getattr(match, f"{phase_name}_game")

                if phase is None:
                    continue

                duration = self._phase_duration(phase)

                if duration <= 0:
                    continue

                deaths_per_10 = (
                    phase.deaths / duration
                ) * 10

                phase_rates[phase_name].append(deaths_per_10)

        averages = {
            phase: self._average(values)
            for phase, values in phase_rates.items()
        }

        valid_phases = {
            phase: rate
            for phase, rate in averages.items()
            if rate is not None
        }

        if len(valid_phases) < 2:
            return None

        highest_phase = max(
            valid_phases,
            key=valid_phases.get
        )

        other_rates = [
            rate
            for phase, rate in valid_phases.items()
            if phase != highest_phase
        ]

        comparison_rate = self._average(other_rates)

        difference = (
            valid_phases[highest_phase] - comparison_rate
        )

        if difference < self.DEATH_RATE_DIFFERENCE_THRESHOLD:
            return None

        return CoachingRecommendation(
            id=f"deaths_{role.lower()}",
            category="deaths",
            title=f"Higher {highest_phase}-game death rate",
            observation=(
                f"Your average death rate during the "
                f"{highest_phase} game is "
                f"{valid_phases[highest_phase]:.2f} per 10 minutes, "
                f"compared with {comparison_rate:.2f} in the "
                f"other analyzed phases."
            ),
            action=(
                "Review deaths in this phase and check positioning, "
                "vision, enemy threats, teammate proximity, and "
                "objective timings before committing to fights."
            ),
            priority="medium",
            confidence=self._confidence(len(matches)),
            matches_analyzed=len(matches),
            evidence=[
                RecommendationEvidence(
                    metric=f"{highest_phase}_deaths_per_10_minutes",
                    value=round(
                        valid_phases[highest_phase],
                        2
                    ),
                ),
                RecommendationEvidence(
                    metric="comparison_deaths_per_10_minutes",
                    value=round(comparison_rate, 2),
                ),
                RecommendationEvidence(
                    metric="role",
                    value=role,
                ),
            ],
        )

    def _generate_exploratory_insights(self, role, matches):
        insights = []

        for match in matches:
            insight = self._analyze_match_farming(role, match)

            if insight is not None:
                insights.append(insight)

        return insights

    def get_coaching_overview(self, riot_account_id):
        timeline = (
            self.timeline_service.get_player_timeline_overview(
                riot_account_id
            )
        )

        role_groups = self._group_by_role(timeline.matches)

        insights = []
        recommendations = []

        for role, matches in role_groups.items():
            if len(matches) >= self.MIN_INSIGHT_MATCHES:
                insights.extend(
                    self._generate_exploratory_insights(
                        role,
                        matches
                    )
                )

            consistency_insight = self._analyze_farming_consistency(
                role,
                matches
            )

            if consistency_insight is not None:
                insights.append(consistency_insight)

            variability_insight = self._analyze_farming_variability(
                role,
                matches
            )

            if variability_insight is not None:
                insights.append(variability_insight)

            farming = self._analyze_farming(role, matches)
            deaths = self._analyze_deaths(role, matches)

            if farming is not None:
                recommendations.append(farming)

            if deaths is not None:
                recommendations.append(deaths)

        insights.sort(
            key=lambda item: item.matches_analyzed,
            reverse=True
        )

        recommendations.sort(
            key=lambda item: (
                item.matches_analyzed,
                item.category == "farming",
            ),
            reverse=True
        )

        return CoachingOverview(
            riot_account_id=riot_account_id,
            total_matches_analyzed=timeline.total_matches,
            insights=insights[:self.MAX_INSIGHTS],
            recommendations=recommendations[
                :self.MAX_RECOMMENDATIONS
            ],
        )

    
    def _analyze_farming_consistency(self, role, matches):
        if len(matches) < self.MIN_CONSISTENCY_MATCHES:
            return None

        phase_rates = {
            "early": [],
            "mid": [],
            "late": [],
        }

        transition_results = {
            "early_to_mid": [],
            "mid_to_late": [],
        }

        for match in matches:
            rates = {}

            for phase_name in phase_rates:
                phase = getattr(match, f"{phase_name}_game")

                if (
                    phase is None
                    or self._phase_duration(phase) <= 0
                    or phase.cs_per_minute is None
                ):
                    continue

                rate = float(phase.cs_per_minute)

                rates[phase_name] = rate
                phase_rates[phase_name].append(rate)

            for transition, previous, current in [
                ("early_to_mid", "early", "mid"),
                ("mid_to_late", "mid", "late"),
            ]:
                if previous not in rates or current not in rates:
                    continue

                previous_rate = rates[previous]
                current_rate = rates[current]

                if previous_rate <= 0:
                    continue

                change = (
                    (current_rate - previous_rate)
                    / previous_rate
                ) * 100

                transition_results[transition].append(change)

        phase_averages = {
            phase: self._average(values)
            for phase, values in phase_rates.items()
        }

        eligible_transitions = []

        for transition, changes in transition_results.items():
            if not changes:
                continue

            decline_count = sum(
                1
                for change in changes
                if change <= -self.CONSISTENCY_DROP_THRESHOLD
            )

            frequency = (
                decline_count / len(changes)
            ) * 100

            eligible_transitions.append({
                "transition": transition,
                "changes": changes,
                "decline_count": decline_count,
                "frequency": frequency,
            })

        if not eligible_transitions:
            return None

        # Identify the transition with the highest observed
        # frequency of significant farming declines.
        selected = max(
            eligible_transitions,
            key=lambda item: (
                item["frequency"],
                item["decline_count"],
            )
        )

        if selected["frequency"] < self.MIN_PATTERN_FREQUENCY:
            return None

        transition_labels = {
            "early_to_mid": ("early", "mid"),
            "mid_to_late": ("mid", "late"),
        }

        previous, current = transition_labels[
            selected["transition"]
        ]

        previous_average = phase_averages[previous]
        current_average = phase_averages[current]

        if (
            previous_average is None
            or current_average is None
        ):
            return None

        average_change = (
            (current_average - previous_average)
            / previous_average
        ) * 100 if previous_average > 0 else 0

        if selected["frequency"] >= 75 and len(matches) >= 10:
            confidence = "moderate"
        else:
            confidence = "low"

        return CoachingInsight(
            id=f"farming_consistency_{role.lower()}",
            category="consistency",
            title=f"Recurring {current}-game farming decline",
            observation=(
                f"A CS/min decline of at least "
                f"{self.CONSISTENCY_DROP_THRESHOLD:.0f}% "
                f"occurred in {selected['decline_count']} of "
                f"{len(selected['changes'])} eligible "
                f"{role} matches during the transition from "
                f"{previous} to {current} game. "
                f"The average CS/min changed from "
                f"{previous_average:.2f} to "
                f"{current_average:.2f} across the analyzed matches."
            ),
            confidence=confidence,
            matches_analyzed=len(matches),
            role=role,
            matches_with_pattern=selected["decline_count"],
            pattern_frequency_percent=round(
                selected["frequency"],
                2
            ),
            evidence=[
                RecommendationEvidence(
                    metric=f"{previous}_average_cs_per_minute",
                    value=round(previous_average, 2),
                ),
                RecommendationEvidence(
                    metric=f"{current}_average_cs_per_minute",
                    value=round(current_average, 2),
                ),
                RecommendationEvidence(
                    metric="average_cs_rate_change_percent",
                    value=round(average_change, 2),
                ),
                RecommendationEvidence(
                    metric="pattern_frequency_percent",
                    value=round(selected["frequency"], 2),
                ),
                RecommendationEvidence(
                    metric="role",
                    value=role,
                ),
            ],
        )

    
    def _analyze_farming_variability(self, role, matches):
        if len(matches) < self.MIN_VARIABILITY_MATCHES:
            return None

        phase_values = {
            "early": [],
            "mid": [],
            "late": [],
        }

        for match in matches:
            for phase_name in phase_values:
                phase = getattr(
                    match,
                    f"{phase_name}_game"
                )

                if (
                    phase is None
                    or self._phase_duration(phase) <= 0
                    or phase.cs_per_minute is None
                ):
                    continue

                phase_values[phase_name].append(
                    float(phase.cs_per_minute)
                )

        results = []

        for phase_name, values in phase_values.items():

            if len(values) < self.MIN_VARIABILITY_MATCHES:
                continue

            average = self._average(values)

            if average is None or average <= 0:
                continue

            standard_deviation = stdev(values)

            coefficient_of_variation = (
                standard_deviation / average
            ) * 100

            results.append({
                "phase": phase_name,
                "average": average,
                "standard_deviation": standard_deviation,
                "cv": coefficient_of_variation,
                "sample_count": len(values),
            })

        if not results:
            return None

        highest_variability = max(
            results,
            key=lambda item: item["cv"]
        )

        if (
            highest_variability["cv"]
            < self.HIGH_VARIABILITY_CV_THRESHOLD
        ):
            return None

        phase = highest_variability["phase"]
        average = highest_variability["average"]
        std_dev = highest_variability["standard_deviation"]
        cv = highest_variability["cv"]
        sample_count = highest_variability["sample_count"]

        confidence = (
            "moderate"
            if sample_count >= 10
            else "low"
        )

        return CoachingInsight(
            id=f"farming_variability_{role.lower()}_{phase}",
            category="consistency",
            title=f"{phase.title()}-game farming variability",
            observation=(
                f"Your {phase}-game CS/min varied across "
                f"{sample_count} {role} matches. "
                f"The average was {average:.2f} CS/min, "
                f"with a standard deviation of "
                f"{std_dev:.2f} and a coefficient of "
                f"variation of {cv:.2f}%."
            ),
            confidence=confidence,
            matches_analyzed=sample_count,
            role=role,
            evidence=[
                RecommendationEvidence(
                    metric=f"{phase}_average_cs_per_minute",
                    value=round(average, 2),
                ),
                RecommendationEvidence(
                    metric=f"{phase}_cs_standard_deviation",
                    value=round(std_dev, 2),
                ),
                RecommendationEvidence(
                    metric=f"{phase}_cs_coefficient_of_variation",
                    value=round(cv, 2),
                ),
            ],
        )