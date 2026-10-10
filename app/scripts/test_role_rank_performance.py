from app.analysis.role_rank_performance_analyzer import (
    RoleRankPerformanceAnalyzer,
)


def main():

    analyzer = (
        RoleRankPerformanceAnalyzer()
    )

    # ==========================================
    # Example Gold ADC game
    # ==========================================

    result = analyzer.analyze(
        rank="GOLD",

        role="BOTTOM",

        features={
            "cs_at_10":
                70,

            "gold_at_10":
                3500,

            "xp_at_10":
                3100,

            "cs_per_min":
                7.4,

            "gold_per_min":
                475,

            "deaths":
                5,

            "kda":
                3.2,
        },
    )

    print()
    print(
        "ROLE / RANK PERFORMANCE"
    )
    print(
        "=" * 60
    )

    print()
    print(
        f"Rank: "
        f"{result['rank']}"
    )

    print(
        f"Role: "
        f"{result['role']}"
    )

    print()
    print(
        "METRICS"
    )

    for metric in (
        result[
            "metrics"
        ]
    ):

        print()

        print(
            f"{metric['metric']}: "
            f"{metric['value']}"
        )

        print(
            f"  Peer percentile: "
            f"{metric['peer_percentile']}"
        )

        print(
            f"  Peer status: "
            f"{metric['peer_status']}"
        )

        print(
            f"  Peer median: "
            f"{metric['peer_median']}"
        )

        print(
            f"  Next rank: "
            f"{metric['next_rank']}"
        )

        print(
            f"  Next rank percentile: "
            f"{metric['next_rank_percentile']}"
        )

        print(
            f"  Next status: "
            f"{metric['next_rank_status']}"
        )

        print(
            f"  Trajectory reliability: "
            f"{metric['trajectory_reliability']}"
        )

        print(
            f"  Trajectory alignment: "
            f"{metric['trajectory_alignment']}"
        )

        print(
            f"  Rank relevance: "
            f"{metric['rank_relevance']}"
        )

    print()
    print(
        "=" * 60
    )

    print()
    print(
        "STRENGTHS"
    )

    for item in (
        result[
            "strengths"
        ]
    ):

        print(
            f"- {item['metric']} "
            f"({item['peer_percentile']}th)"
        )

    print()
    print(
        "NEXT-RANK COMPETITIVE"
    )

    for item in (
        result[
            "next_rank_ready"
        ]
    ):

        print(
            f"- {item['metric']} "
            f"({item['next_rank_percentile']}th "
            f"vs {item['next_rank']}, "
            f"rank relevance="
            f"{item['rank_relevance']})"
        )

    print()
    print(
        "RANK-ALIGNED STRENGTHS"
    )

    for item in (
        result[
            "rank_aligned_strengths"
        ]
    ):

        print(
            f"- {item['metric']} "
            f"(peer="
            f"{item['peer_percentile']}th, "
            f"next="
            f"{item['next_rank_percentile']}th, "
            f"relevance="
            f"{item['rank_relevance']})"
        )

    print()
    print(
        "DEVELOPMENT OPPORTUNITIES"
    )

    if not (
        result[
            "development_opportunities"
        ]
    ):

        print(
            "- No supported basic-stat "
            "development gap detected."
        )

    else:

        for item in (
            result[
                "development_opportunities"
            ]
        ):

            print(
                f"- {item['metric']} "
                f"(peer="
                f"{item['peer_percentile']}th, "
                f"next="
                f"{item['next_rank_percentile']}th, "
                f"relevance="
                f"{item['rank_relevance']})"
            )

    print()
    print(
        "DESCRIPTIVE ONLY"
    )

    for item in (
        result[
            "descriptive_only"
        ]
    ):

        print(
            f"- {item['metric']} "
            f"(peer="
            f"{item['peer_percentile']}th, "
            f"relevance="
            f"{item['rank_relevance']})"
        )


if __name__ == "__main__":
    main()