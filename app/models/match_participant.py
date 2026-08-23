from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "participant_id",
            name="uq_match_participant",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    puuid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    participant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    champion_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    champion_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    champion_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    role: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    lane: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    win: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    kills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    deaths: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    assists: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_gold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    gold_earned: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_minions_killed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    neutral_minions_killed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_damage_dealt: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_damage_dealt_to_champions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_damage_taken: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    damage_self_mitigated: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    physical_damage_dealt_to_champions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    magic_damage_dealt_to_champions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    true_damage_dealt_to_champions: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    wards_placed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    wards_killed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    detector_wards_placed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    item_0: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_3: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_4: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_5: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_6: Mapped[int | None] = mapped_column(Integer, nullable=True)

    summoner1_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    summoner2_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    match = relationship(
        "Match",
        back_populates="participants",
    )