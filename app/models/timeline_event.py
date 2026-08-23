from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    real_timestamp_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    participant_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    killer_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    victim_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    team_id: Mapped[int | None] = mapped_column(
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
        back_populates="timeline_events",
    )