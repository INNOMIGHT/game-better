from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class LeagueProfile(Base):
    __tablename__ = "league_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    riot_account_id: Mapped[int] = mapped_column(
        ForeignKey("riot_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    summoner_level: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    profile_icon_id: Mapped[int | None] = mapped_column(
        Integer,
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

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    riot_account = relationship(
        "RiotAccount",
        back_populates="league_profile",
    )