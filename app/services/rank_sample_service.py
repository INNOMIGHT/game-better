from app.ml.rank_baselines import (
    RankedPlayerSample,
)


class RankSampleService:

    STANDARD_TIERS = {
        "GOLD",
        "PLATINUM",
        "EMERALD",
        "DIAMOND",
    }

    DIVISIONS = [
        "I",
        "II",
        "III",
        "IV",
    ]

    def __init__(
        self,
        riot_client,
    ):

        self.riot_client = (
            riot_client
        )

    # ==================================================
    # NORMAL LADDER
    # ==================================================

    def collect_standard_tier_players(
        self,
        *,
        platform,
        tier,
        target_players=100,
    ):

        tier = tier.upper()

        if tier not in self.STANDARD_TIERS:

            raise ValueError(
                f"Unsupported standard tier: {tier}"
            )

        players_by_division = {
            division: []
            for division in self.DIVISIONS
        }

        seen_puuids = set()

        target_per_division = max(
            target_players
            // len(
                self.DIVISIONS
            ),
            1,
        )

        # ==========================================
        # COLLECT PLAYERS PER DIVISION
        # ==========================================

        for division in self.DIVISIONS:

            page = 1

            while (
                len(
                    players_by_division[
                        division
                    ]
                )
                < target_per_division
            ):

                entries = (
                    self.riot_client
                    .get_ranked_entries(
                        platform=platform,
                        tier=tier,
                        division=division,
                        page=page,
                    )
                )

                if not entries:
                    break

                for entry in entries:

                    puuid = entry.get(
                        "puuid"
                    )

                    if not puuid:
                        continue

                    if puuid in seen_puuids:
                        continue

                    seen_puuids.add(
                        puuid
                    )

                    players_by_division[
                        division
                    ].append(
                        RankedPlayerSample(
                            puuid=puuid,

                            tier=tier,

                            division=division,

                            league_points=
                                entry.get(
                                    "leaguePoints"
                                ),

                            wins=
                                entry.get(
                                    "wins"
                                ),

                            losses=
                                entry.get(
                                    "losses"
                                ),

                            platform=platform,

                            rank_bucket=tier,
                        )
                    )

                    if (
                        len(
                            players_by_division[
                                division
                            ]
                        )
                        >= target_per_division
                    ):
                        break

                page += 1

        # ==========================================
        # INTERLEAVE DIVISIONS
        #
        # I, II, III, IV,
        # I, II, III, IV...
        #
        # This prevents the match collector from
        # exhausting the target before reaching IV.
        # ==========================================

        players = []

        max_count = max(
            (
                len(items)
                for items
                in players_by_division.values()
            ),
            default=0,
        )

        for index in range(
            max_count
        ):

            for division in self.DIVISIONS:

                division_players = (
                    players_by_division[
                        division
                    ]
                )

                if (
                    index
                    >= len(
                        division_players
                    )
                ):
                    continue

                players.append(
                    division_players[
                        index
                    ]
                )

                if (
                    len(players)
                    >= target_players
                ):

                    return players

        return players


    # ==================================================
    # MASTER+
    # ==================================================

    def collect_master_plus_players(
        self,
        *,
        platform,
        target_players=100,
    ):

        players = []

        seen = set()

        # Prefer distribution across all three
        # elite ladders rather than only Challenger.

        sources = [
            (
                "MASTER",
                self.riot_client
                .get_master_league,
            ),
            (
                "GRANDMASTER",
                self.riot_client
                .get_grandmaster_league,
            ),
            (
                "CHALLENGER",
                self.riot_client
                .get_challenger_league,
            ),
        ]

        target_per_source = max(
            target_players
            // len(
                sources
            ),
            1,
        )

        for (
            tier,
            getter,
        ) in sources:

            league = getter(
                platform=platform
            )

            entries = (
                league.get(
                    "entries",
                    []
                )
            )

            count = 0

            for entry in entries:

                # Depending on LeagueListDTO version,
                # elite entries may expose summonerId
                # rather than PUUID.
                #
                # We'll resolve that below.

                puuid = entry.get(
                    "puuid"
                )

                if not puuid:

                    summoner_id = (
                        entry.get(
                            "summonerId"
                        )
                    )

                    if not summoner_id:
                        continue

                    summoner = (
                        self.riot_client
                        .get_summoner_by_id(
                            platform=platform,
                            summoner_id=
                                summoner_id,
                        )
                    )

                    puuid = (
                        summoner.get(
                            "puuid"
                        )
                    )

                if not puuid:
                    continue

                if puuid in seen:
                    continue

                seen.add(
                    puuid
                )

                players.append(
                    RankedPlayerSample(
                        puuid=puuid,

                        tier=tier,

                        division=None,

                        league_points=
                            entry.get(
                                "leaguePoints"
                            ),

                        wins=
                            entry.get(
                                "wins"
                            ),

                        losses=
                            entry.get(
                                "losses"
                            ),

                        platform=platform,

                        rank_bucket=
                            "MASTER_PLUS",
                    )
                )

                count += 1

                if (
                    count
                    >= target_per_source
                ):
                    break

        return players[
            :target_players
        ]