from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.database.database import Base


class TimelineFrame(Base):
    __tablename__ = "timeline_frames"

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "participant_id",
            "timestamp_ms",
            name="uq_timeline_frame",
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

    participant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    timestamp_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    current_gold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_gold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    gold_per_second: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    xp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    minions_killed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    jungle_minions_killed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    position_x: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    position_y: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    champion_stats: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    damage_stats: Mapped[dict | None] = mapped_column(
        JSONB,
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
        back_populates="timeline_frames",
    )