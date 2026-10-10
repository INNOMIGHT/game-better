from app.database.database import (
    SessionLocal,
)

from app.repositories.analytics_repository import (
    AnalyticsRepository,
)

from app.analysis.match_analysis_service import (
    MatchAnalysisService,
)


# ==================================================
# CONFIG
# ==================================================

RIOT_ACCOUNT_ID = 1

PLAYER_RANK = "GOLD"

MATCH_LIMIT = 1


def main():

    db = SessionLocal()

    try:

        repository = (
            AnalyticsRepository(
                db
            )
        )

        service = (
            MatchAnalysisService(
                db=db
            )
        )

        # ==================================================
        # RIOT ACCOUNT + PROFILE
        # ==================================================

        account_result = (
            repository
            .get_riot_account(
                RIOT_ACCOUNT_ID
            )
        )

        if account_result is None:

            raise RuntimeError(
                "Riot account not found."
            )

        # get_riot_account() returns:
        #
        # (RiotAccount, LeagueProfile)
        #
        # SQLAlchemy Row supports tuple unpacking.

        riot_account, league_profile = (
            account_result
        )

        print()
        print(
            "ACCOUNT"
        )
        print(
            "=" * 60
        )

        print(
            f"Riot account id: "
            f"{riot_account.id}"
        )

        print(
            f"PUUID: "
            f"{riot_account.puuid}"
        )

        print(
            f"Game name: "
            f"{riot_account.game_name}"
        )

        print(
            f"Tag line: "
            f"{riot_account.tag_line}"
        )

        print(
            f"Platform: "
            f"{league_profile.platform}"
        )

        print(
            f"Region: "
            f"{league_profile.region}"
        )

        # ==================================================
        # RECENT PLAYER MATCHES
        # ==================================================

        match_results = (
            repository
            .get_player_matches(
                puuid=
                    riot_account.puuid,

                limit=
                    MATCH_LIMIT,
            )
        )

        if not match_results:

            raise RuntimeError(
                "No ranked matches found "
                "for this Riot account."
            )

        # Repository already gives us:
        #
        # {
        #     "match": Match,
        #     "player": MatchParticipant,
        #     "participants": [...]
        # }

        selected = (
            match_results[0]
        )

        match = (
            selected[
                "match"
            ]
        )

        participant = (
            selected[
                "player"
            ]
        )

        all_participants = (
            selected[
                "participants"
            ]
        )

        # ==================================================
        # TIMELINE
        # ==================================================

        all_frames = (
            repository
            .get_timeline_frames(
                [
                    match.id
                ]
            )
        )

        all_events = (
            repository
            .get_timeline_events(
                [
                    match.id
                ]
            )
        )

        # ----------------------------------------------
        # Player frames only
        # ----------------------------------------------

        player_frames = [
            frame
            for frame in all_frames
            if (
                frame.match_id
                == match.id
                and
                frame.participant_id
                == participant.participant_id
            )
        ]

        # ----------------------------------------------
        # Critical/positive analyzers need access to
        # match-wide timeline context.
        #
        # For now we pass all match events.
        # ----------------------------------------------

        match_events = [
            event
            for event in all_events
            if (
                event.match_id
                == match.id
            )
        ]

        # ==================================================
        # REPORT RAW INPUT
        # ==================================================

        print()
        print(
            "MATCH INPUT"
        )
        print(
            "=" * 60
        )

        print(
            f"Internal match id: "
            f"{match.id}"
        )

        print(
            f"Riot match id: "
            f"{match.match_id}"
        )

        print(
            f"Champion: "
            f"{participant.champion_name}"
        )

        print(
            f"Role: "
            f"{participant.role}"
        )

        print(
            f"Win: "
            f"{participant.win}"
        )

        print(
            f"Participants loaded: "
            f"{len(all_participants)}"
        )

        print(
            f"Player frames loaded: "
            f"{len(player_frames)}"
        )

        print(
            f"Events loaded: "
            f"{len(match_events)}"
        )

        if not player_frames:

            raise RuntimeError(
                "No timeline frames found "
                "for selected player."
            )

        # ==================================================
        # FIRST UNIFIED ANALYSIS
        #
        # FARM / ECON / death-pattern outputs are still
        # empty here intentionally.
        #
        # First we validate orchestration:
        #
        # performance
        # critical moments
        # positive moments
        # rank performance
        # coaching signals
        # loss context
        # ==================================================

        analysis = (
            service
            .analyze_match(
                match=
                    match,

                participant=
                    participant,

                player_frames=
                    player_frames,

                all_participants=
                    all_participants,

                all_frames=
                    all_frames,

                events=
                    match_events,

                rank=
                    PLAYER_RANK,

                role=
                    participant.role,
            )
        )
        # ==================================================
        # FINAL OUTPUT
        # ==================================================

        print()
        print()
        print(
            "DIFFTHEORY MATCH ANALYSIS"
        )
        print(
            "Beyond The Stats"
        )
        print(
            "=" * 60
        )

        print(
            f"Match: "
            f"{analysis['match_id']}"
        )

        print(
            f"Champion: "
            f"{analysis['champion']}"
        )

        print(
            f"Role: "
            f"{analysis['role']}"
        )

        print(
            f"Rank: "
            f"{analysis['rank']}"
        )

        print(
            f"Win: "
            f"{analysis['win']}"
        )

        # ==================================================
        # RANK PERFORMANCE
        # ==================================================

        print()
        print(
            "RANK PERFORMANCE"
        )
        print(
            "-" * 60
        )

        rank_performance = (
            analysis.get(
                "rank_performance"
            )
        )

        if not rank_performance:

            print(
                "No supported rank-relative "
                "analysis available."
            )

        else:

            for metric in (
                rank_performance.get(
                    "metrics",
                    [],
                )
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
                    f"  Next rank: "
                    f"{metric['next_rank']}"
                )

                print(
                    f"  Next percentile: "
                    f"{metric['next_rank_percentile']}"
                )

                print(
                    f"  Rank relevance: "
                    f"{metric['rank_relevance']}"
                )

        # ==================================================
        # COACHING SIGNALS
        # ==================================================

        print()
        print(
            "COACHING SIGNALS"
        )
        print(
            "-" * 60
        )

        coaching_signals = (
            analysis.get(
                "coaching_signals",
                [],
            )
        )

        if not coaching_signals:

            print(
                "No coaching signals generated."
            )

        else:

            for signal in (
                coaching_signals
            ):

                prefix = (
                    "+"
                    if signal.get(
                        "positive"
                    )
                    else "-"
                )

                print()

                print(
                    f"{prefix} "
                    f"{signal.get('key')}"
                )

                print(
                    f"  "
                    f"{signal.get('title')}"
                )

                print(
                    f"  Category: "
                    f"{signal.get('category')}"
                )

                print(
                    f"  Severity: "
                    f"{signal.get('severity')}"
                )

                print(
                    f"  Source: "
                    f"{signal.get('source')}"
                )

                if (
                    signal.get(
                        "minute"
                    )
                    is not None
                ):

                    print(
                        f"  Minute: "
                        f"{signal.get('minute')}"
                    )

        # ==================================================
        # CRITICAL MOMENTS
        # ==================================================

        print()
        print(
            "CRITICAL MOMENTS"
        )
        print(
            "-" * 60
        )

        critical_moments = (
            analysis.get(
                "critical_moments",
                [],
            )
        )

        print(
            f"Count: "
            f"{len(critical_moments)}"
        )

        for moment in (
            critical_moments[
                :5
            ]
        ):

            print()

            print(
                moment
            )

        # ==================================================
        # POSITIVE MOMENTS
        # ==================================================

        print()
        print(
            "POSITIVE MOMENTS"
        )
        print(
            "-" * 60
        )

        positive_moments = (
            analysis.get(
                "positive_moments",
                [],
            )
        )

        print(
            f"Count: "
            f"{len(positive_moments)}"
        )

        for moment in (
            positive_moments[
                :5
            ]
        ):

            print()

            print(
                moment
            )

        # ==================================================
        # IMPACT
        # ==================================================

        print()
        print(
            "IMPACT SUMMARY"
        )
        print(
            "-" * 60
        )

        print(
            analysis.get(
                "impact_summary"
            )
        )

        # ==================================================
        # RECOMMENDATIONS
        # ==================================================

        print()
        print(
            "MATCH RECOMMENDATIONS"
        )
        print(
            "-" * 60
        )

        recommendations = (
            analysis.get(
                "recommendations",
                [],
            )
        )

        if not recommendations:

            print(
                "No match recommendations."
            )

        else:

            for recommendation in (
                recommendations
            ):

                print()

                print(
                    recommendation
                )

        # ==================================================
        # LOSS CONTEXT
        # ==================================================

        if (
            analysis.get(
                "loss_context"
            )
            is not None
        ):

            print()
            print(
                "LOSS CONTEXT"
            )
            print(
                "-" * 60
            )

            print(
                analysis[
                    "loss_context"
                ]
            )

    finally:

        db.close()


if __name__ == "__main__":

    main()