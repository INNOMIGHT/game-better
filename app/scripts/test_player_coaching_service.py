from app.database.database import (
    SessionLocal,
)

from app.repositories.analytics_repository import (
    AnalyticsRepository,
)

from app.analysis.match_analysis_service import (
    MatchAnalysisService,
)

from app.analysis.player_coaching_service import (
    PlayerCoachingService,
)


RIOT_ACCOUNT_ID = 1

PLAYER_RANK = "GOLD"

MATCH_LIMIT = 10


def main():

    db = SessionLocal()

    try:

        repository = (
            AnalyticsRepository(
                db
            )
        )

        match_analysis_service = (
            MatchAnalysisService(
                db=db
            )
        )

        player_coaching_service = (
            PlayerCoachingService()
        )

        # ==================================================
        # ACCOUNT
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

        riot_account, league_profile = (
            account_result
        )

        print()

        print(
            "DIFFTHEORY PLAYER COACHING TEST"
        )

        print(
            "=" * 70
        )

        print(
            f"Player: "
            f"{riot_account.game_name}"
            f"#{riot_account.tag_line}"
        )

        print(
            f"Rank: "
            f"{PLAYER_RANK}"
        )

        # ==================================================
        # MATCHES
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
                "No ranked matches found."
            )

        print(
            f"Matches loaded: "
            f"{len(match_results)}"
        )

        match_ids = [
            item[
                "match"
            ].id
            for item in match_results
        ]

        # ==================================================
        # LOAD ALL TIMELINE DATA ONCE
        # ==================================================

        all_frames = (
            repository
            .get_timeline_frames(
                match_ids
            )
        )

        all_events = (
            repository
            .get_timeline_events(
                match_ids
            )
        )

        # ==================================================
        # GROUP TIMELINE DATA BY MATCH
        # ==================================================

        frames_by_match = {}

        for frame in all_frames:

            frames_by_match.setdefault(
                frame.match_id,
                [],
            ).append(
                frame
            )

        events_by_match = {}

        for event in all_events:

            events_by_match.setdefault(
                event.match_id,
                [],
            ).append(
                event
            )

        # ==================================================
        # ANALYZE EACH MATCH
        # ==================================================

        analyses = []

        print()
        print(
            "MATCH ANALYSES"
        )

        print(
            "-" * 70
        )

        for index, item in enumerate(
            match_results,
            start=1,
        ):

            match = (
                item[
                    "match"
                ]
            )

            participant = (
                item[
                    "player"
                ]
            )

            participants = (
                item[
                    "participants"
                ]
            )

            match_frames = (
                frames_by_match.get(
                    match.id,
                    [],
                )
            )

            match_events = (
                events_by_match.get(
                    match.id,
                    [],
                )
            )

            player_frames = [
                frame
                for frame in match_frames
                if (
                    frame.participant_id
                    ==
                    participant.participant_id
                )
            ]

            if not player_frames:

                print(
                    f"{index}. "
                    f"{match.match_id} "
                    f"SKIPPED - no player frames"
                )

                continue

            analysis = (
                match_analysis_service
                .analyze_match(
                    match=
                        match,

                    participant=
                        participant,

                    player_frames=
                        player_frames,

                    all_participants=
                        participants,

                    all_frames=
                        match_frames,

                    events=
                        match_events,

                    rank=
                        PLAYER_RANK,

                    role=
                        participant.role,
                )
            )

            analyses.append(
                analysis
            )

            print(
                f"{index}. "
                f"{match.match_id} | "
                f"{participant.champion_name} | "
                f"{participant.role} | "
                f"{'WIN' if participant.win else 'LOSS'} | "
                f"{len(analysis.get('coaching_signals', []))} signals"
            )

        # ==================================================
        # PLAYER COACHING
        # ==================================================

        coaching = (
            player_coaching_service
            .build(
                analyses
            )
        )

        print()
        print()

        print(
            "DIFFTHEORY PLAYER COACHING"
        )

        print(
            "Beyond The Stats"
        )

        print(
            "=" * 70
        )

        print(
            f"Matches analyzed: "
            f"{coaching['matches_analyzed']}"
        )

        record = (
            coaching[
                "record"
            ]
        )

        print(
            f"Record: "
            f"{record['wins']}W "
            f"{record['losses']}L"
        )

        print(
            f"Win rate: "
            f"{round(record['win_rate'] * 100, 1)}%"
        )

        # ==================================================
        # TOP 3 PRIORITIES
        # ==================================================

        print()
        print(
            "TOP 3 PRIORITIES"
        )

        print(
            "-" * 70
        )

        top_priorities = (
            coaching[
                "top_priorities"
            ]
        )

        if not top_priorities:

            print(
                "No recurring priorities found."
            )

        for index, priority in enumerate(
            top_priorities,
            start=1,
        ):

            print()

            print(
                f"{index}. "
                f"{priority['title']}"
            )

            print(
                f"   Score: "
                f"{priority['priority_score']}/10"
            )

            print(
                f"   Matches affected: "
                f"{priority['matches_affected']}"
                f"/"
                f"{priority['matches_analyzed']}"
            )

            print(
                f"   Frequency: "
                f"{round(priority['frequency'] * 100, 1)}%"
            )

            print(
                f"   Average intensity: "
                f"{round(priority['average_intensity'] * 100, 1)}%"
            )

            print(
                f"   Evidence types: "
                f"{', '.join(priority['signal_types'])}"
            )

            trend = (
                priority[
                    "trend"
                ]
            )

            print(
                f"   Trend: "
                f"{trend['direction']}"
            )

            if (
                trend.get(
                    "recent_intensity"
                )
                is not None
            ):

                print(
                    f"   Recent intensity: "
                    f"{round(trend['recent_intensity'] * 100, 1)}%"
                )

                print(
                    f"   Older intensity: "
                    f"{round(trend['older_intensity'] * 100, 1)}%"
                )

                print(
                    f"   Intensity change: "
                    f"{round(trend['change'] * 100, 1)} pts"
                )

            print(
                f"   Action: "
                f"{priority['action']}"
            )

        # ==================================================
        # VIEW ALL
        # ==================================================

        if coaching[
            "has_more_priorities"
        ]:

            print()

            print(
                f"VIEW ALL "
                f"("
                f"{coaching['remaining_priority_count']} "
                f"MORE"
                f")"
            )

            print(
                "-" * 70
            )

            for index, priority in enumerate(
                coaching[
                    "all_priorities"
                ][3:],
                start=4,
            ):

                print(
                    f"{index}. "
                    f"{priority['title']} | "
                    f"{priority['priority_score']}/10 | "
                    f"{priority['matches_affected']}/"
                    f"{priority['matches_analyzed']} matches | "
                    f"{priority['trend']['direction']}"
                )

        # ==================================================
        # STRENGTHS
        # ==================================================

        print()
        print(
            "STRENGTHS"
        )

        print(
            "-" * 70
        )

        strengths = (
            coaching[
                "strengths"
            ]
        )

        if not strengths:

            print(
                "No recurring strengths found."
            )

        else:

            for strength in strengths:

                print()

                print(
                    f"+ "
                    f"{strength['title']}"
                )

                print(
                    f"  Strength score: "
                    f"{strength['strength_score']}/10"
                )

                print(
                    f"  Supported in: "
                    f"{strength['matches_supported']}/"
                    f"{strength['matches_analyzed']} matches"
                )

                print(
                    f"  Frequency: "
                    f"{round(strength['frequency'] * 100, 1)}%"
                )

                print(
                    f"  Average intensity: "
                    f"{round(strength['average_intensity'] * 100, 1)}%"
                )

                print(
                    f"  Evidence: "
                    f"{', '.join(strength['signal_types'])}"
                )

        # ==================================================
        # MIXED / INCONSISTENT PATTERNS
        # ==================================================

        print()
        print(
            "MIXED / INCONSISTENT PATTERNS"
        )

        print(
            "-" * 70
        )

        mixed_patterns = (
            coaching.get(
                "mixed_patterns",
                [],
            )
        )

        if not mixed_patterns:

            print(
                "No major mixed patterns found."
            )

        else:

            for pattern in mixed_patterns:

                print()

                print(
                    f"~ "
                    f"{pattern['title']}"
                )

                print(
                    f"  Classification: "
                    f"{pattern['classification']}"
                )

                print(
                    f"  Negative score: "
                    f"{pattern['negative_score']}/10"
                )

                print(
                    f"  Positive score: "
                    f"{pattern['positive_score']}/10"
                )

                print(
                    f"  Negative matches: "
                    f"{pattern['negative_matches']}/"
                    f"{pattern['matches_analyzed']}"
                )

                print(
                    f"  Positive matches: "
                    f"{pattern['positive_matches']}/"
                    f"{pattern['matches_analyzed']}"
                )

                print(
                    f"  Negative frequency: "
                    f"{round(pattern['negative_frequency'] * 100, 1)}%"
                )

                print(
                    f"  Positive frequency: "
                    f"{round(pattern['positive_frequency'] * 100, 1)}%"
                )

                print(
                    f"  Negative evidence: "
                    f"{', '.join(pattern['negative_signal_types'])}"
                )

                print(
                    f"  Positive evidence: "
                    f"{', '.join(pattern['positive_signal_types'])}"
                )

                print(
                    f"  Interpretation: "
                    f"{pattern['interpretation']}"
                )

        # ==================================================
        # ROLE BREAKDOWN
        # ==================================================

        print()
        print(
            "ROLE BREAKDOWN"
        )

        print(
            "-" * 70
        )

        role_breakdown = (
            coaching.get(
                "role_breakdown",
                {},
            )
        )

        if not role_breakdown:

            print(
                "No role-specific analysis available."
            )

        else:

            for (
                role,
                profile,
            ) in role_breakdown.items():

                print()

                print(
                    f"{role} "
                    f"("
                    f"{profile['matches_analyzed']} matches"
                    f")"
                )

                role_record = (
                    profile.get(
                        "record",
                        {},
                    )
                )

                if role_record:

                    print(
                        f"  Record: "
                        f"{role_record.get('wins', 0)}W "
                        f"{role_record.get('losses', 0)}L"
                    )

                role_priorities = (
                    profile.get(
                        "top_priorities",
                        [],
                    )
                )

                if not role_priorities:

                    print(
                        "  No strong recurring priorities."
                    )

                else:

                    print(
                        "  Top priorities:"
                    )

                    for (
                        priority_index,
                        priority,
                    ) in enumerate(
                        role_priorities,
                        start=1,
                    ):

                        print(
                            f"    "
                            f"{priority_index}. "
                            f"{priority['title']} "
                            f"- "
                            f"{priority['priority_score']}/10 "
                            f"("
                            f"{priority['matches_affected']}/"
                            f"{priority['matches_analyzed']}"
                            f")"
                        )

                role_strengths = (
                    profile.get(
                        "strengths",
                        [],
                    )
                )

                if role_strengths:

                    print(
                        "  Strengths:"
                    )

                    for strength in (
                        role_strengths[:3]
                    ):

                        print(
                            f"    + "
                            f"{strength['title']} "
                            f"- "
                            f"{strength['strength_score']}/10"
                        )

                role_mixed = (
                    profile.get(
                        "mixed_patterns",
                        [],
                    )
                )

                if role_mixed:

                    print(
                        "  Mixed patterns:"
                    )

                    for pattern in (
                        role_mixed[:3]
                    ):

                        print(
                            f"    ~ "
                            f"{pattern['title']} "
                            f"| negative "
                            f"{pattern['negative_score']} "
                            f"| positive "
                            f"{pattern['positive_score']}"
                        )

        # ==================================================
        # CATEGORY SUMMARY
        # ==================================================

        print()
        print(
            "CATEGORY SUMMARY"
        )

        print(
            "-" * 70
        )

        category_summary = (
            coaching.get(
                "category_summary",
                {},
            )
        )

        if not category_summary:

            print(
                "No priority categories available."
            )

        else:

            for (
                category,
                summary,
            ) in (
                category_summary.items()
            ):

                print(
                    f"{category}: "
                    f"{summary['priority_count']} themes | "
                    f"highest score "
                    f"{summary['highest_score']}"
                )

    finally:

        db.close()


if __name__ == "__main__":

    main()