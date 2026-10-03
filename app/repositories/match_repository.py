
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.match_team import MatchTeam
from app.models.match_participant import MatchParticipant
from app.models.timeline_frame import TimelineFrame
from app.models.timeline_event import TimelineEvent


def timestamp_to_datetime(value):
    if value is None:
        return None

    return datetime.fromtimestamp(
        value / 1000,
        tz=timezone.utc,
    ).replace(tzinfo=None)


class MatchRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_match_id(self, match_id: str):
        return (
            self.db.query(Match)
            .filter(Match.match_id == match_id)
            .first()
        )

    def save_match(
        self,
        match_data: dict,
        timeline_data: dict,
    ) -> Match:

        metadata = match_data["metadata"]
        info = match_data["info"]
        timeline_info = timeline_data["info"]

        match = Match(
            match_id=metadata["matchId"],
            data_version=metadata.get("dataVersion"),
            game_id=info.get("gameId"),
            game_version=info.get("gameVersion"),
            game_creation=timestamp_to_datetime(
                info.get("gameCreation")
            ),
            game_start_timestamp=timestamp_to_datetime(
                info.get("gameStartTimestamp")
            ),
            game_end_timestamp=timestamp_to_datetime(
                info.get("gameEndTimestamp")
            ),
            game_duration=info.get("gameDuration"),
            game_mode=info.get("gameMode"),
            game_type=info.get("gameType"),
            queue_id=info["queueId"],
            map_id=info.get("mapId"),
            platform_id=info.get("platformId"),
            end_of_game_result=info.get("endOfGameResult"),
            raw_data={
                "match": match_data,
                "timeline": timeline_data,
            },
        )

        self.db.add(match)
        self.db.flush()

        # -------------------------
        # Teams
        # -------------------------

        for team_data in info.get("teams", []):

            objectives = team_data.get("objectives", {})

            def first_objective(name):
                objective = objectives.get(name, {})
                return objective.get("first")

            team = MatchTeam(
                match_id=match.id,
                team_id=team_data["teamId"],
                win=team_data["win"],
                first_blood=first_objective("champion"),
                first_tower=first_objective("tower"),
                first_dragon=first_objective("dragon"),
                first_baron=first_objective("baron"),
                first_rift_herald=first_objective("riftHerald"),
                first_inhibitor=first_objective("inhibitor"),
            )

            self.db.add(team)

        # -------------------------
        # Participants
        # -------------------------

        for participant_data in info.get("participants", []):

            participant = MatchParticipant(
                match_id=match.id,
                puuid=participant_data["puuid"],
                participant_id=participant_data["participantId"],
                team_id=participant_data["teamId"],
                champion_id=participant_data["championId"],
                champion_name=participant_data.get("championName"),
                champion_level=participant_data.get("champLevel"),
                role=participant_data.get("teamPosition"),
                lane=participant_data.get("lane"),
                win=participant_data["win"],
                kills=participant_data.get("kills", 0),
                deaths=participant_data.get("deaths", 0),
                assists=participant_data.get("assists", 0),
                total_gold=participant_data.get("goldSpent"),
                gold_earned=participant_data.get("goldEarned"),
                total_minions_killed=participant_data.get(
                    "totalMinionsKilled"
                ),
                neutral_minions_killed=participant_data.get(
                    "neutralMinionsKilled"
                ),
                total_damage_dealt=participant_data.get(
                    "totalDamageDealt"
                ),
                total_damage_dealt_to_champions=participant_data.get(
                    "totalDamageDealtToChampions"
                ),
                total_damage_taken=participant_data.get(
                    "totalDamageTaken"
                ),
                damage_self_mitigated=participant_data.get(
                    "damageSelfMitigated"
                ),
                physical_damage_dealt_to_champions=participant_data.get(
                    "physicalDamageDealtToChampions"
                ),
                magic_damage_dealt_to_champions=participant_data.get(
                    "magicDamageDealtToChampions"
                ),
                true_damage_dealt_to_champions=participant_data.get(
                    "trueDamageDealtToChampions"
                ),
                wards_placed=participant_data.get("wardsPlaced"),
                wards_killed=participant_data.get("wardsKilled"),
                detector_wards_placed=participant_data.get(
                    "detectorWardsPlaced"
                ),
                item_0=participant_data.get("item0"),
                item_1=participant_data.get("item1"),
                item_2=participant_data.get("item2"),
                item_3=participant_data.get("item3"),
                item_4=participant_data.get("item4"),
                item_5=participant_data.get("item5"),
                item_6=participant_data.get("item6"),
                summoner1_id=participant_data.get("summoner1Id"),
                summoner2_id=participant_data.get("summoner2Id"),
                raw_data=participant_data,
            )

            self.db.add(participant)

        # -------------------------
        # Timeline frames
        # -------------------------

        for frame in timeline_info.get("frames", []):

            timestamp_ms = frame["timestamp"]

            for participant_key, frame_data in (
                frame.get("participantFrames", {}).items()
            ):

                participant_id = int(participant_key)

                position = frame_data.get("position") or {}

                timeline_frame = TimelineFrame(
                    match_id=match.id,
                    participant_id=participant_id,
                    timestamp_ms=timestamp_ms,
                    current_gold=frame_data.get("currentGold"),
                    total_gold=frame_data.get("totalGold"),
                    gold_per_second=frame_data.get("goldPerSecond"),
                    level=frame_data.get("level"),
                    xp=frame_data.get("xp"),
                    minions_killed=frame_data.get("minionsKilled"),
                    jungle_minions_killed=frame_data.get(
                        "jungleMinionsKilled"
                    ),
                    position_x=position.get("x"),
                    position_y=position.get("y"),
                    champion_stats=frame_data.get("championStats"),
                    damage_stats=frame_data.get("damageStats"),
                    raw_data=frame_data,
                )

                self.db.add(timeline_frame)

        # -------------------------
        # Timeline events
        # -------------------------

        for frame in timeline_info.get("frames", []):

            for event in frame.get("events", []):

                position = event.get("position") or {}

                event_type = event.get("type")

                if not event_type:
                    continue

                timeline_event = TimelineEvent(
                    match_id=match.id,
                    timestamp_ms=event.get(
                        "timestamp",
                        frame["timestamp"],
                    ),
                    real_timestamp_ms=event.get("realTimestamp"),
                    event_type=event_type,
                    participant_id=event.get("participantId"),
                    killer_id=event.get("killerId"),
                    victim_id=event.get("victimId"),
                    team_id=event.get("teamId"),
                    position_x=position.get("x"),
                    position_y=position.get("y"),
                    raw_data=event,
                )

                self.db.add(timeline_event)

        self.db.flush()

        return match