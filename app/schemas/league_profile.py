from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeagueProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    riot_account_id: int
    platform: str
    region: str
    summoner_level: int | None
    profile_icon_id: int | None
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime | None