"""Diligence MCP Connector — 14 tools for AI agent integration.

Runs as a separate Docker container on port 3001. Proxies all requests
to the backend FastAPI service via internal Docker network.
"""
from __future__ import annotations

import os
import json
import httpx
from datetime import date
from mcp.server.fastmcp import FastMCP

FITNESS_API_URL = os.getenv("FITNESS_API_URL", "http://backend:8000")

mcp = FastMCP("Diligence Fitness", port=3001)

# Internal HTTP client — talks to the backend on the Docker network
_client: httpx.AsyncClient | None = None

async def api(method: str, path: str, **kwargs) -> dict:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=FITNESS_API_URL, timeout=30)
    # TODO: add service account API key auth header
    resp = await getattr(_client, method)(f"/api{path}", **kwargs)
    resp.raise_for_status()
    return resp.json()


# ── CONTEXT & STATUS (3 tools) ───────────────────────────────────────────

@mcp.tool()
async def get_context() -> str:
    """Get full user profile, motivation type, program status, point rules, rewards, and integration status. Call this at the start of each conversation to understand the user's current state."""
    data = await api("get", "/points/today")
    profile = await api("get", "/onboarding/profile")
    rewards = await api("get", "/points/rewards")
    integrations = await api("get", "/integrations/status")
    meal_plan = None
    try:
        meal_plan = await api("get", "/meal-plans/today")
    except Exception:
        pass

    return json.dumps({
        "user": profile,
        "today": data,
        "rewards": rewards,
        "integrations": integrations,
        "active_meal_plan": meal_plan,
    }, indent=2, default=str)


@mcp.tool()
async def get_today(date_str: str | None = None) -> str:
    """Get today's points earned, daily gate status (passed/not), breakdown by category, and activities logged/remaining. Optionally pass a date (YYYY-MM-DD) to check a different day."""
    params = {"date": date_str} if date_str else {}
    data = await api("get", "/points/today", params=params)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_week(start_date: str | None = None) -> str:
    """Get weekly summary including total points, active days count, target progress, and day-by-day breakdown."""
    params = {"start_date": start_date} if start_date else {}
    data = await api("get", "/points/week", params=params)
    return json.dumps(data, indent=2, default=str)


# ── ACTIVITY LOGGING (1 tool) ────────────────────────────────────────────

@mcp.tool()
async def log_activity(
    category: str,
    title: str,
    duration_minutes: int,
    notes: str | None = None,
    date_str: str | None = None,
    program_day: int | None = None,
) -> str:
    """Log a workout or activity. Returns points earned and daily total.

    Args:
        category: Type of activity (workout, cardio, yoga, walking, cycling, swimming, other)
        title: Description of what was done (e.g. "Bench press and squats")
        duration_minutes: How long the activity lasted
        notes: Optional additional notes
        date_str: Optional date (YYYY-MM-DD), defaults to today
        program_day: Optional program day number to mark a program workout complete
    """
    payload = {
        "category": category,
        "title": title,
        "duration_minutes": duration_minutes,
    }
    if notes:
        payload["notes"] = notes
    if date_str:
        payload["date"] = date_str
    if program_day:
        payload["program_day"] = program_day

    data = await api("post", "/activities/log", json=payload)
    return json.dumps(data, indent=2, default=str)


# ── FOOD & NUTRITION (2 tools) ───────────────────────────────────────────

@mcp.tool()
async def log_food(
    meal_type: str,
    food_name: str,
    calories: int | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
    servings: float | None = None,
    plan_item_id: str | None = None,
) -> str:
    """Log a food item with optional nutrition data.

    Args:
        meal_type: One of breakfast, lunch, dinner, snack
        food_name: What was eaten
        calories: Estimated calories
        protein_g: Grams of protein
        carbs_g: Grams of carbohydrates
        fat_g: Grams of fat
        servings: Number of servings (default 1)
        plan_item_id: Optional meal plan item ID to link compliance
    """
    payload = {"meal_type": meal_type, "food_name": food_name}
    if calories is not None:
        payload["calories"] = calories
    if protein_g is not None:
        payload["protein_g"] = protein_g
    if carbs_g is not None:
        payload["carbs_g"] = carbs_g
    if fat_g is not None:
        payload["fat_g"] = fat_g
    if servings is not None:
        payload["servings"] = servings
    if plan_item_id:
        payload["plan_item_id"] = plan_item_id

    data = await api("post", "/food/log", json=payload)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def search_food(query: str) -> str:
    """Search for food items in Open Food Facts and USDA FoodData Central. Returns nutrition data for matching items."""
    data = await api("get", "/food/search", params={"q": query})
    return json.dumps(data, indent=2, default=str)


# ── PROGRAMS (1 tool) ────────────────────────────────────────────────────

@mcp.tool()
async def get_program_schedule(date_str: str | None = None) -> str:
    """Get today's scheduled workout from the active program, including exercises with sets, reps, and weight progression. Shows upcoming workouts and overall completion percentage."""
    params = {"date": date_str} if date_str else {}
    data = await api("get", "/programs/schedule", params=params)
    return json.dumps(data, indent=2, default=str)


# ── REWARDS (1 tool) ─────────────────────────────────────────────────────

@mcp.tool()
async def redeem_reward(reward_name: str) -> str:
    """Spend points on a configured reward. Returns success/failure and remaining points.

    Args:
        reward_name: Name of the reward to redeem (e.g. "1 hour gaming")
    """
    data = await api("post", "/points/rewards/redeem", json={"name": reward_name})
    return json.dumps(data, indent=2, default=str)


# ── MEAL PLANS (4 tools) ─────────────────────────────────────────────────

@mcp.tool()
async def load_meal_plan(
    name: str,
    duration_days: int,
    meals: list[dict],
    diet_type: str | None = None,
    daily_calories: int | None = None,
    restrictions: list[str] | None = None,
) -> str:
    """Create a complete meal plan with all items. The AI agent generates the plan content; this tool stores it for tracking.

    Args:
        name: Plan name (e.g. "7-Day Dairy-Free Keto")
        duration_days: How many days the plan covers
        meals: List of meal items, each with day_number, meal_type, food_name, calories, protein_g, carbs_g, fat_g
        diet_type: Optional diet type (keto, paleo, balanced, custom)
        daily_calories: Optional daily calorie target
        restrictions: Optional list of dietary restrictions
    """
    payload = {
        "name": name,
        "duration_days": duration_days,
        "meals": meals,
    }
    if diet_type:
        payload["diet_type"] = diet_type
    if daily_calories:
        payload["daily_calories"] = daily_calories
    if restrictions:
        payload["restrictions"] = restrictions

    data = await api("post", "/meal-plans", json=payload)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_meal_plan(date_str: str | None = None) -> str:
    """View the active meal plan's meals for today or a specified date."""
    if date_str:
        # TODO: pass date to API when supported
        pass
    data = await api("get", "/meal-plans/today")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def update_meal_compliance(
    plan_item_id: str,
    status: str,
    substitution: str | None = None,
) -> str:
    """Mark a planned meal as followed, substituted, or skipped.

    Args:
        plan_item_id: The meal plan item ID
        status: One of 'followed', 'substituted', 'skipped'
        substitution: What was eaten instead (required if status is 'substituted')
    """
    payload = {"plan_item_id": plan_item_id, "status": status}
    if substitution:
        payload["substitution"] = substitution
    data = await api("post", "/meal-plans/compliance", json=payload)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_plan_progress(plan_id: str | None = None) -> str:
    """Get overall compliance stats for a meal plan: percentage followed, days completed, average calories vs target."""
    if plan_id:
        data = await api("get", f"/meal-plans/{plan_id}/progress")
    else:
        # Get active plan progress
        plans = await api("get", "/meal-plans")
        active = next((p for p in plans if p.get("status") == "active"), None)
        if not active:
            return json.dumps({"error": "No active meal plan"})
        data = await api("get", f"/meal-plans/{active['id']}/progress")
    return json.dumps(data, indent=2, default=str)


# ── INTEGRATIONS (2 tools) ───────────────────────────────────────────────

@mcp.tool()
async def configure_integration(provider: str, credentials: dict) -> str:
    """Store encrypted integration credentials. Write-only — credentials can be set but never read back.

    Args:
        provider: Provider name (strava, polar, garmin, fitbit, usda, telegram, groq, etc.)
        credentials: Dict of credential fields (e.g. {"client_id": "...", "client_secret": "..."})
    """
    data = await api("post", "/integrations/configure", json={
        "provider": provider,
        "credentials": credentials,
    })
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def get_integration_status() -> str:
    """Check connection status of all integration providers. Never returns actual credential values."""
    data = await api("get", "/integrations/status")
    return json.dumps(data, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport="sse")
