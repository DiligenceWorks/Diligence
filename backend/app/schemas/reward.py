from datetime import date
from pydantic import BaseModel


class RewardCreate(BaseModel):
    name: str
    description: str | None = None
    point_cost: int


class RewardResponse(BaseModel):
    id: str
    name: str
    description: str | None
    point_cost: int
    is_active: bool

    model_config = {"from_attributes": True}


class RewardRedeemRequest(BaseModel):
    date: date | None = None  # defaults to today


class RedemptionResponse(BaseModel):
    id: str
    reward_name: str
    points_spent: int
    redemption_date: date
