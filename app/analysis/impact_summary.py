class ImpactSummary:

    @staticmethod
    def build(
        critical_moments,
        positive_moments,
    ):

        negative_scores = [
            moment.get(
                "severity",
                0,
            )
            for moment
            in critical_moments
        ]

        positive_scores = [
            moment.get(
                "impact_score",
                0,
            )
            for moment
            in positive_moments
        ]

        negative_total = sum(
            negative_scores
        )

        positive_total = sum(
            positive_scores
        )

        return {
            "positive_moment_count":
                len(
                    positive_scores
                ),

            "negative_moment_count":
                len(
                    negative_scores
                ),

            "positive_impact_total":
                positive_total,

            "negative_impact_total":
                negative_total,

            "max_positive_impact":
                max(
                    positive_scores,
                    default=0,
                ),

            "max_negative_impact":
                max(
                    negative_scores,
                    default=0,
                ),

            "net_impact":
                (
                    positive_total
                    - negative_total
                ),
        }