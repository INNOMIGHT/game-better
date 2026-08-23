from datetime import datetime

from sqlalchemy import DateTime, Integer, String, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    match_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    data_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    game_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    game_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    game_creation: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    game_start_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    game_end_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    game_duration: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    game_mode: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    game_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    queue_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    map_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    platform_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    end_of_game_result: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    teams = relationship(
        "MatchTeam",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    participants = relationship(
        "MatchParticipant",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    timeline_frames = relationship(
        "TimelineFrame",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    timeline_events = relationship(
        "TimelineEvent",
        back_populates="match",
        cascade="all, delete-orphan",
    )