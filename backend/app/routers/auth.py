from __future__ import annotations

import logging
import traceback
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.points import PointRule, DailyTarget, DEFAULT_POINT_RULES, TTM_DAILY_TARGETS
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.utils.auth import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger("fitness-rewards")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(req: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        existing = await db.execute(select(User).where(User.username == req.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

        user = User(
            username=req.username,
            display_name=req.display_name,
            password_hash=hash_password(req.password),
            email=req.email,
        )
        db.add(user)
        await db.flush()

        # Create empty profile
        profile = UserProfile(user_id=user.id)
        db.add(profile)

        # Create default point rules
        for rule_data in DEFAULT_POINT_RULES:
            db.add(PointRule(user_id=user.id, **rule_data))

        # Create default daily targets
        db.add(DailyTarget(user_id=user.id))

        await db.flush()
        token = create_access_token(str(user.id))
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Registration failed: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": tb})


@router.post("/login")
async def login(req: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        result = await db.execute(select(User).where(User.username == req.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = create_access_token(str(user.id))
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Login failed: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": tb})


@router.get("/me")
async def get_me(user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "timezone": user.timezone,
    }
