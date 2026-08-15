from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiotAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    puuid: str
    game_name: str
    tag_line: str
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime | None = None