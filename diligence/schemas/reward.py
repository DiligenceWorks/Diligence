from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class RewardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    point_cost: int


class RewardResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    point_cost: int
    is_active: bool

    model_config = {"from_attributes": True}


class RewardRedeemRequest(BaseModel):
    redemption_date: Optional[date] = Field(None, alias="date")


class RedemptionResponse(BaseModel):
    id: str
    reward_name: str
    points_spent: int
    redemption_date: date
