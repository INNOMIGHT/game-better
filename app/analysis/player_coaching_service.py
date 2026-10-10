from collections import defaultdict


class PlayerCoachingService:

    # ==================================================
    # CONFIGURATION
    # ==================================================

    TOP_PRIORITY_COUNT = 3

    MIN_NEGATIVE_SEVERITY = 3
    MIN_POSITIVE_SEVERITY = 3

    # A theme can still qualify with lower-severity
    # evidence if multiple independent signal types
    # support it inside the same match.
    LOW_SEVERITY_DIVERSITY_THRESHOLD = 2

    RECENCY_DECAY = 0.90

    # Positive and negative theme scores within this
    # distance may be treated as inconsistent/mixed,
    # provided both occur often enough.
    MIXED_SCORE_MARGIN = 1.5

    MIXED_MIN_FREQUENCY = 0.25

    # ==================================================
    # THEME CONFIG
    # ==================================================

    THEME_CONFIG = {

        "fight_selection": {
            "title":
                "Fight Selection",

            "category":
                "FIGHT_SELECTION",

            "description":
                (
                    "Improve when and where you commit "
                    "to fights."
                ),

            "action":
                (
                    "Before committing, check team gold, "
                    "levels, nearby numbers and whether "
                    "teammates can realistically follow."
                ),
        },

        "survival": {
            "title":
                "Survival & Death Impact",

            "category":
                "SURVIVAL",

            "description":
                (
                    "Reduce deaths that occur during "
                    "high-impact game states."
                ),

            "action":
                (
                    "Prioritize surviving when your death "
                    "could remove map pressure or worsen "
                    "an already difficult game state."
                ),
        },

        "objective_survival": {
            "title":
                "Objective-Window Survival",

            "category":
                "OBJECTIVES",

            "description":
                (
                    "Stay available during important "
                    "objective windows."
                ),

            "action":
                (
                    "Avoid unnecessary risks shortly "
                    "before Dragon, Herald or Baron."
                ),
        },

        "resource_recovery": {
            "title":
                "Resource Recovery",

            "category":
                "ECONOMY",

            "description":
                (
                    "Recover farming and economic tempo "
                    "after disruptions."
                ),

            "action":
                (
                    "After combat, deaths or rotations, "
                    "look for the safest route back into "
                    "consistent gold and experience gain."
                ),
        },

        "farming": {
            "title":
                "Farming Consistency",

            "category":
                "FARMING",

            "description":
                (
                    "Improve consistency of resource "
                    "collection throughout the match."
                ),

            "action":
                (
                    "Reduce extended low-CS periods and "
                    "maintain resource collection between "
                    "fights and objectives."
                ),
        },

        "economy": {
            "title":
                "Economic Efficiency",

            "category":
                "ECONOMY",

            "description":
                (
                    "Improve sustained gold generation "
                    "relative to your role and rank."
                ),

            "action":
                (
                    "Look for higher-value resource "
                    "collection between major map events "
                    "and reduce unnecessary downtime."
                ),
        },

        "combat": {
            "title":
                "Combat Efficiency",

            "category":
                "COMBAT",

            "description":
                (
                    "Improve the value generated from "
                    "combat participation."
                ),

            "action":
                (
                    "Focus on higher-value fights rather "
                    "than simply increasing combat "
                    "frequency."
                ),
        },

        "early_progression": {
            "title":
                "Early-Game Progression",

            "category":
                "EARLY_GAME",

            "description":
                (
                    "Improve early resource and experience "
                    "progression."
                ),

            "action":
                (
                    "Build repeatable early-game habits "
                    "that produce reliable lane or map "
                    "progression."
                ),
        },

        "objective_conversion": {
            "title":
                "Objective Conversion",

            "category":
                "OBJECTIVES",

            "description":
                (
                    "Convert successful fights into "
                    "meaningful map value."
                ),

            "action":
                (
                    "Continue looking for Dragon, Baron, "
                    "Herald or structure opportunities "
                    "after successful combat."
                ),
        },
    }

    # ==================================================
    # SIGNAL → THEME
    # ==================================================

    SIGNAL_THEME_MAP = {

        # Fight selection
        "fight_while_gold_behind":
            "fight_selection",

        "fight_while_level_behind":
            "fight_selection",

        "outnumbered_fight":
            "fight_selection",

        # Survival
        "high_impact_death":
            "survival",

        "level_gap_widening":
            "survival",

        "repeated_deaths_early":
            "survival",

        "repeated_deaths_mid":
            "survival",

        "repeated_deaths_late":
            "survival",

        "survival_efficiency":
            "survival",

        # Objective survival
        "death_before_objective":
            "objective_survival",

        # Positive objective conversion
        "successful_objective_conversion":
            "objective_conversion",

        # Recovery
        "farm_recovery_failure":
            "resource_recovery",

        "economic_recovery_failure":
            "resource_recovery",

        "farm_recovery_success":
            "resource_recovery",

        "economic_recovery_success":
            "resource_recovery",

        # Farming
        "farm_disruption":
            "farming",

        "early_farming":
            "farming",

        "sustained_farming":
            "farming",

        # Economy
        "economic_disruption":
            "economy",

        "early_economy":
            "economy",

        "sustained_economy":
            "economy",

        # Experience
        "early_experience":
            "early_progression",

        # Combat
        "combat_efficiency":
            "combat",
    }

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _clamp(
        value,
        minimum,
        maximum,
    ):

        return max(
            minimum,
            min(
                value,
                maximum,
            ),
        )

    @staticmethod
    def _round_score(
        value,
    ):

        return round(
            value,
            2,
        )

    def _recency_weights(
        self,
        count,
    ):

        return [
            self.RECENCY_DECAY ** index
            for index in range(
                count
            )
        ]

    # ==================================================
    # SIGNAL NORMALIZATION
    # ==================================================

    def _normalize_signal(
        self,
        signal,
    ):

        if not isinstance(
            signal,
            dict,
        ):
            return None

        key = (
            signal.get(
                "key"
            )
        )

        if not key:
            return None

        theme = (
            self.SIGNAL_THEME_MAP.get(
                key
            )
        )

        if theme is None:
            return None

        severity = (
            signal.get(
                "severity",
                3,
            )
            or 3
        )

        try:

            severity = int(
                severity
            )

        except (
            TypeError,
            ValueError,
        ):

            severity = 3

        severity = (
            self._clamp(
                severity,
                1,
                5,
            )
        )

        return {
            "key":
                key,

            "theme":
                theme,

            "category":
                signal.get(
                    "category"
                ),

            "title":
                signal.get(
                    "title"
                ),

            "severity":
                severity,

            "minute":
                signal.get(
                    "minute"
                ),

            "source":
                signal.get(
                    "source"
                ),

            "positive":
                bool(
                    signal.get(
                        "positive",
                        False,
                    )
                ),

            "evidence":
                signal.get(
                    "evidence",
                    {},
                )
                or {},
        }

    # ==================================================
    # MATCH GROUPING
    # ==================================================

    def _group_match_signals(
        self,
        match_analysis,
    ):

        negative = defaultdict(
            list
        )

        positive = defaultdict(
            list
        )

        for raw_signal in (
            match_analysis.get(
                "coaching_signals",
                [],
            )
            or []
        ):

            signal = (
                self._normalize_signal(
                    raw_signal
                )
            )

            if signal is None:
                continue

            theme = (
                signal[
                    "theme"
                ]
            )

            if signal[
                "positive"
            ]:

                positive[
                    theme
                ].append(
                    signal
                )

            else:

                negative[
                    theme
                ].append(
                    signal
                )

        return {
            "negative":
                negative,

            "positive":
                positive,
        }

    # ==================================================
    # MATCH THEME QUALIFICATION
    # ==================================================

    def _theme_qualifies(
        self,
        signals,
        *,
        positive,
    ):
        """
        Avoid marking a whole match as affected because
        of one weak severity-2 detector result.

        A theme qualifies when:

        1. At least one sufficiently strong signal exists

        OR

        2. Multiple independent signal types support it.
        """

        if not signals:
            return False

        threshold = (
            self.MIN_POSITIVE_SEVERITY
            if positive
            else self.MIN_NEGATIVE_SEVERITY
        )

        max_severity = max(
            signal[
                "severity"
            ]
            for signal in signals
        )

        if max_severity >= threshold:
            return True

        signal_types = {
            signal[
                "key"
            ]
            for signal in signals
        }

        if (
            len(
                signal_types
            )
            >=
            self.LOW_SEVERITY_DIVERSITY_THRESHOLD
        ):

            return True

        return False

    # ==================================================
    # PER-MATCH THEME INTENSITY
    # ==================================================

    def _theme_intensity(
        self,
        signals,
    ):
        """
        Return normalized intensity from 0.0 → 1.0.

        We do NOT sum every signal.

        That prevents one chaotic game containing dozens
        of duplicate observations from dominating the
        player's profile.
        """

        if not signals:
            return 0.0

        max_severity = max(
            signal[
                "severity"
            ]
            for signal in signals
        )

        average_severity = (
            sum(
                signal[
                    "severity"
                ]
                for signal in signals
            )
            /
            len(
                signals
            )
        )

        signal_types = {
            signal[
                "key"
            ]
            for signal in signals
        }

        severity_component = (
            max_severity
            / 5
        )

        average_component = (
            average_severity
            / 5
        )

        diversity_component = min(
            len(
                signal_types
            )
            / 3,
            1.0,
        )

        intensity = (
            0.55
            * severity_component

            +

            0.25
            * average_component

            +

            0.20
            * diversity_component
        )

        return self._clamp(
            intensity,
            0.0,
            1.0,
        )

    # ==================================================
    # TREND
    # ==================================================

    @staticmethod
    def _calculate_intensity_trend(
        intensities,
    ):
        """
        Intensities are newest-first.

        Unlike the previous implementation, this looks
        at HOW STRONG the theme was in each match rather
        than only True/False presence.
        """

        if len(
            intensities
        ) < 4:

            return {
                "direction":
                    "INSUFFICIENT_DATA",

                "recent_intensity":
                    None,

                "older_intensity":
                    None,

                "change":
                    None,
            }

        split = max(
            2,
            len(
                intensities
            )
            // 2,
        )

        recent = (
            intensities[
                :split
            ]
        )

        older = (
            intensities[
                split:
            ]
        )

        if not older:

            return {
                "direction":
                    "INSUFFICIENT_DATA",

                "recent_intensity":
                    None,

                "older_intensity":
                    None,

                "change":
                    None,
            }

        recent_average = (
            sum(
                recent
            )
            / len(
                recent
            )
        )

        older_average = (
            sum(
                older
            )
            / len(
                older
            )
        )

        change = (
            recent_average
            - older_average
        )

        if change <= -0.12:

            direction = (
                "IMPROVING"
            )

        elif change >= 0.12:

            direction = (
                "WORSENING"
            )

        else:

            direction = (
                "STABLE"
            )

        return {
            "direction":
                direction,

            "recent_intensity":
                round(
                    recent_average,
                    3,
                ),

            "older_intensity":
                round(
                    older_average,
                    3,
                ),

            "change":
                round(
                    change,
                    3,
                ),
        }

    # ==================================================
    # EVIDENCE BUILDER
    # ==================================================

    @staticmethod
    def _build_evidence_item(
        match,
        signal,
    ):

        return {
            "match_id":
                match.get(
                    "match_id"
                ),

            "champion":
                match.get(
                    "champion"
                ),

            "role":
                match.get(
                    "role"
                ),

            "win":
                match.get(
                    "win"
                ),

            "key":
                signal[
                    "key"
                ],

            "title":
                signal[
                    "title"
                ],

            "severity":
                signal[
                    "severity"
                ],

            "minute":
                signal[
                    "minute"
                ],

            "source":
                signal[
                    "source"
                ],

            "evidence":
                signal[
                    "evidence"
                ],
        }

    # ==================================================
    # NEGATIVE THEME
    # ==================================================

    def _build_priority(
        self,
        *,
        theme,
        matches,
        grouped_matches,
        recency_weights,
    ):

        total_matches = len(
            matches
        )

        affected_indices = []

        per_match_intensities = []

        qualifying_intensities = []

        all_signal_types = set()

        evidence = []

        for index, grouped in enumerate(
            grouped_matches
        ):

            signals = (
                grouped[
                    "negative"
                ].get(
                    theme,
                    [],
                )
            )

            intensity = (
                self._theme_intensity(
                    signals
                )
            )

            per_match_intensities.append(
                intensity
            )

            if not self._theme_qualifies(
                signals,
                positive=False,
            ):

                continue

            affected_indices.append(
                index
            )

            qualifying_intensities.append(
                intensity
            )

            for signal in signals:

                all_signal_types.add(
                    signal[
                        "key"
                    ]
                )

                evidence.append(
                    self._build_evidence_item(
                        matches[
                            index
                        ],
                        signal,
                    )
                )

        if not affected_indices:
            return None

        # ==========================================
        # FREQUENCY
        # ==========================================

        frequency = (
            len(
                affected_indices
            )
            / total_matches
        )

        # ==========================================
        # INTENSITY
        # ==========================================

        average_intensity = (
            sum(
                qualifying_intensities
            )
            /
            len(
                qualifying_intensities
            )
        )

        # ==========================================
        # RECENCY
        # ==========================================

        total_recency_weight = sum(
            recency_weights
        )

        affected_recency_weight = sum(
            recency_weights[
                index
            ]
            for index
            in affected_indices
        )

        recency_score = (
            affected_recency_weight
            / total_recency_weight
            if total_recency_weight
            else 0
        )

        # ==========================================
        # EVIDENCE DIVERSITY
        # ==========================================

        diversity_score = min(
            len(
                all_signal_types
            )
            / 4,
            1.0,
        )

        # ==========================================
        # FINAL SCORE
        # ==========================================

        raw_score = (
            0.35
            * frequency

            +

            0.30
            * average_intensity

            +

            0.20
            * recency_score

            +

            0.15
            * diversity_score
        )

        priority_score = (
            raw_score
            * 10
        )

        config = (
            self.THEME_CONFIG[
                theme
            ]
        )

        evidence.sort(
            key=lambda item: (
                item.get(
                    "severity",
                    0,
                ),
                -(
                    item.get(
                        "minute"
                    )
                    or 999
                ),
            ),
            reverse=True,
        )

        return {
            "key":
                theme,

            "title":
                config[
                    "title"
                ],

            "category":
                config[
                    "category"
                ],

            "description":
                config[
                    "description"
                ],

            "action":
                config[
                    "action"
                ],

            "priority_score":
                self._round_score(
                    priority_score
                ),

            "matches_affected":
                len(
                    affected_indices
                ),

            "matches_analyzed":
                total_matches,

            "frequency":
                round(
                    frequency,
                    3,
                ),

            "average_intensity":
                round(
                    average_intensity,
                    3,
                ),

            "signal_types":
                sorted(
                    all_signal_types
                ),

            "signal_type_count":
                len(
                    all_signal_types
                ),

            "evidence_count":
                len(
                    evidence
                ),

            "examples":
                evidence[
                    :5
                ],

            "all_evidence":
                evidence,

            "trend":
                self._calculate_intensity_trend(
                    per_match_intensities
                ),
        }

    # ==================================================
    # POSITIVE THEME
    # ==================================================

    def _build_strength(
        self,
        *,
        theme,
        matches,
        grouped_matches,
        recency_weights,
    ):

        total_matches = len(
            matches
        )

        supported_indices = []

        qualifying_intensities = []

        signal_types = set()

        evidence = []

        for index, grouped in enumerate(
            grouped_matches
        ):

            signals = (
                grouped[
                    "positive"
                ].get(
                    theme,
                    [],
                )
            )

            if not self._theme_qualifies(
                signals,
                positive=True,
            ):

                continue

            supported_indices.append(
                index
            )

            qualifying_intensities.append(
                self._theme_intensity(
                    signals
                )
            )

            for signal in signals:

                signal_types.add(
                    signal[
                        "key"
                    ]
                )

                evidence.append(
                    self._build_evidence_item(
                        matches[
                            index
                        ],
                        signal,
                    )
                )

        if not supported_indices:
            return None

        frequency = (
            len(
                supported_indices
            )
            / total_matches
        )

        average_intensity = (
            sum(
                qualifying_intensities
            )
            /
            len(
                qualifying_intensities
            )
        )

        total_weight = sum(
            recency_weights
        )

        supported_weight = sum(
            recency_weights[
                index
            ]
            for index
            in supported_indices
        )

        recency_score = (
            supported_weight
            / total_weight
            if total_weight
            else 0
        )

        strength_score = (
            (
                0.45
                * frequency
            )
            +
            (
                0.35
                * average_intensity
            )
            +
            (
                0.20
                * recency_score
            )
        ) * 10

        config = (
            self.THEME_CONFIG[
                theme
            ]
        )

        evidence.sort(
            key=lambda item:
                item.get(
                    "severity",
                    0,
                ),
            reverse=True,
        )

        return {
            "key":
                theme,

            "title":
                config[
                    "title"
                ],

            "category":
                config[
                    "category"
                ],

            "strength_score":
                self._round_score(
                    strength_score
                ),

            "matches_supported":
                len(
                    supported_indices
                ),

            "matches_analyzed":
                total_matches,

            "frequency":
                round(
                    frequency,
                    3,
                ),

            "average_intensity":
                round(
                    average_intensity,
                    3,
                ),

            "signal_types":
                sorted(
                    signal_types
                ),

            "evidence_count":
                len(
                    evidence
                ),

            "examples":
                evidence[
                    :5
                ],

            "all_evidence":
                evidence,
        }

    # ==================================================
    # POSITIVE / NEGATIVE RECONCILIATION
    # ==================================================

    def _reconcile_themes(
        self,
        priorities,
        strengths,
    ):
        """
        Prevent confusing output such as:

        Resource Recovery = major weakness
        Resource Recovery = major strength

        If positive and negative evidence are both
        substantial and close in score, classify the
        theme as MIXED / INCONSISTENT instead.
        """

        priority_by_key = {
            item[
                "key"
            ]:
                item
            for item in priorities
        }

        strength_by_key = {
            item[
                "key"
            ]:
                item
            for item in strengths
        }

        all_keys = (
            set(
                priority_by_key.keys()
            )
            |
            set(
                strength_by_key.keys()
            )
        )

        final_priorities = []

        final_strengths = []

        mixed_patterns = []

        for key in all_keys:

            negative = (
                priority_by_key.get(
                    key
                )
            )

            positive = (
                strength_by_key.get(
                    key
                )
            )

            if negative is None:

                final_strengths.append(
                    positive
                )

                continue

            if positive is None:

                final_priorities.append(
                    negative
                )

                continue

            negative_score = (
                negative[
                    "priority_score"
                ]
            )

            positive_score = (
                positive[
                    "strength_score"
                ]
            )

            negative_frequency = (
                negative[
                    "frequency"
                ]
            )

            positive_frequency = (
                positive[
                    "frequency"
                ]
            )

            score_difference = (
                negative_score
                - positive_score
            )

            both_frequent = (
                negative_frequency
                >= self.MIXED_MIN_FREQUENCY

                and

                positive_frequency
                >= self.MIXED_MIN_FREQUENCY
            )

            if (
                both_frequent
                and
                abs(
                    score_difference
                )
                <= self.MIXED_SCORE_MARGIN
            ):

                config = (
                    self.THEME_CONFIG[
                        key
                    ]
                )

                mixed_patterns.append({
                    "key":
                        key,

                    "title":
                        config[
                            "title"
                        ],

                    "category":
                        config[
                            "category"
                        ],

                    "classification":
                        "INCONSISTENT",

                    "negative_score":
                        negative_score,

                    "positive_score":
                        positive_score,

                    "negative_frequency":
                        negative_frequency,

                    "positive_frequency":
                        positive_frequency,

                    "negative_matches":
                        negative[
                            "matches_affected"
                        ],

                    "positive_matches":
                        positive[
                            "matches_supported"
                        ],

                    "matches_analyzed":
                        negative[
                            "matches_analyzed"
                        ],

                    "negative_signal_types":
                        negative[
                            "signal_types"
                        ],

                    "positive_signal_types":
                        positive[
                            "signal_types"
                        ],

                    "negative_examples":
                        negative[
                            "examples"
                        ],

                    "positive_examples":
                        positive[
                            "examples"
                        ],

                    "interpretation":
                        (
                            f"{config['title']} is inconsistent "
                            "across recent matches: both positive "
                            "and negative evidence appear often."
                        ),
                })

                continue

            # Negative evidence clearly dominates.
            if score_difference > 0:

                final_priorities.append(
                    negative
                )

            # Positive evidence clearly dominates.
            else:

                final_strengths.append(
                    positive
                )

        final_priorities.sort(
            key=lambda item:
                item[
                    "priority_score"
                ],
            reverse=True,
        )

        final_strengths.sort(
            key=lambda item:
                item[
                    "strength_score"
                ],
            reverse=True,
        )

        mixed_patterns.sort(
            key=lambda item:
                max(
                    item[
                        "negative_score"
                    ],
                    item[
                        "positive_score"
                    ],
                ),
            reverse=True,
        )

        return {
            "priorities":
                final_priorities,

            "strengths":
                final_strengths,

            "mixed_patterns":
                mixed_patterns,
        }

    # ==================================================
    # CATEGORY SUMMARY
    # ==================================================

    @staticmethod
    def _build_category_summary(
        priorities,
    ):

        summary = defaultdict(
            lambda: {
                "priority_count": 0,
                "highest_score": 0,
            }
        )

        for priority in priorities:

            category = (
                priority[
                    "category"
                ]
            )

            summary[
                category
            ][
                "priority_count"
            ] += 1

            summary[
                category
            ][
                "highest_score"
            ] = max(
                summary[
                    category
                ][
                    "highest_score"
                ],
                priority[
                    "priority_score"
                ],
            )

        return dict(
            summary
        )

    # ==================================================
    # CORE PROFILE BUILDER
    # ==================================================

    def _build_profile(
        self,
        matches,
    ):

        if not matches:

            return {
                "matches_analyzed": 0,
                "top_priorities": [],
                "all_priorities": [],
                "strengths": [],
                "mixed_patterns": [],
                "category_summary": {},
            }

        grouped_matches = [
            self._group_match_signals(
                match
            )
            for match in matches
        ]

        recency_weights = (
            self._recency_weights(
                len(
                    matches
                )
            )
        )

        negative_themes = set()
        positive_themes = set()

        for grouped in grouped_matches:

            negative_themes.update(
                grouped[
                    "negative"
                ].keys()
            )

            positive_themes.update(
                grouped[
                    "positive"
                ].keys()
            )

        # ==========================================
        # RAW NEGATIVE THEMES
        # ==========================================

        priorities = []

        for theme in (
            negative_themes
        ):

            priority = (
                self._build_priority(
                    theme=
                        theme,

                    matches=
                        matches,

                    grouped_matches=
                        grouped_matches,

                    recency_weights=
                        recency_weights,
                )
            )

            if priority is not None:

                priorities.append(
                    priority
                )

        # ==========================================
        # RAW POSITIVE THEMES
        # ==========================================

        strengths = []

        for theme in (
            positive_themes
        ):

            strength = (
                self._build_strength(
                    theme=
                        theme,

                    matches=
                        matches,

                    grouped_matches=
                        grouped_matches,

                    recency_weights=
                        recency_weights,
                )
            )

            if strength is not None:

                strengths.append(
                    strength
                )

        # ==========================================
        # RECONCILE CONTRADICTIONS
        # ==========================================

        reconciled = (
            self._reconcile_themes(
                priorities,
                strengths,
            )
        )

        priorities = (
            reconciled[
                "priorities"
            ]
        )

        strengths = (
            reconciled[
                "strengths"
            ]
        )

        mixed_patterns = (
            reconciled[
                "mixed_patterns"
            ]
        )

        wins = sum(
            1
            for match in matches
            if match.get(
                "win"
            )
        )

        losses = (
            len(
                matches
            )
            - wins
        )

        return {
            "matches_analyzed":
                len(
                    matches
                ),

            "record": {
                "wins":
                    wins,

                "losses":
                    losses,

                "win_rate":
                    round(
                        wins
                        / len(
                            matches
                        ),
                        3,
                    ),
            },

            # ======================================
            # DEFAULT UI
            # ======================================

            "top_priorities":
                priorities[
                    :self.TOP_PRIORITY_COUNT
                ],

            # ======================================
            # VIEW ALL
            # ======================================

            "all_priorities":
                priorities,

            "has_more_priorities":
                len(
                    priorities
                )
                >
                self.TOP_PRIORITY_COUNT,

            "remaining_priority_count":
                max(
                    len(
                        priorities
                    )
                    -
                    self.TOP_PRIORITY_COUNT,
                    0,
                ),

            # ======================================
            # POSITIVE PROFILE
            # ======================================

            "strengths":
                strengths,

            # ======================================
            # INCONSISTENT BEHAVIOUR
            # ======================================

            "mixed_patterns":
                mixed_patterns,

            "category_summary":
                self._build_category_summary(
                    priorities
                ),
        }

    # ==================================================
    # ROLE BREAKDOWN
    # ==================================================

    def _build_role_breakdown(
        self,
        matches,
    ):

        matches_by_role = defaultdict(
            list
        )

        for match in matches:

            role = (
                match.get(
                    "role"
                )
                or "UNKNOWN"
            )

            matches_by_role[
                str(
                    role
                ).upper()
            ].append(
                match
            )

        role_breakdown = {}

        for (
            role,
            role_matches,
        ) in matches_by_role.items():

            role_profile = (
                self._build_profile(
                    role_matches
                )
            )

            role_breakdown[
                role
            ] = {
                "matches_analyzed":
                    role_profile[
                        "matches_analyzed"
                    ],

                "record":
                    role_profile[
                        "record"
                    ],

                "top_priorities":
                    role_profile[
                        "top_priorities"
                    ],

                "all_priorities":
                    role_profile[
                        "all_priorities"
                    ],

                "strengths":
                    role_profile[
                        "strengths"
                    ],

                "mixed_patterns":
                    role_profile[
                        "mixed_patterns"
                    ],
            }

        return role_breakdown

    # ==================================================
    # PUBLIC API
    # ==================================================

    def build(
        self,
        match_analyses,
    ):
        """
        Match analyses MUST be newest-first.
        """

        matches = [
            analysis
            for analysis in (
                match_analyses or []
            )
            if isinstance(
                analysis,
                dict,
            )
        ]

        profile = (
            self._build_profile(
                matches
            )
        )

        profile[
            "role_breakdown"
        ] = (
            self._build_role_breakdown(
                matches
            )
        )

        return profile

    # ==================================================
    # BACKWARD-COMPATIBILITY
    # ==================================================

    def analyze_recent_matches(
        self,
        match_analyses,
    ):
        """
        Compatibility alias for the previous
        PlayerCoachingService API.
        """

        return self.build(
            match_analyses
        )