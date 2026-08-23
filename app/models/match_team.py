from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class MatchTeam(Base):
    __tablename__ = "match_teams"

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "team_id",
            name="uq_match_team",
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

    team_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    win: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    first_blood: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    first_tower: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    first_dragon: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    first_baron: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    first_rift_herald: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    first_inhibitor: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    match = relationship(
        "Match",
        back_populates="teams",
    )