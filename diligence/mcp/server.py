"""Diligence MCP Server — 14 tools for AI agent integration.

For the pip install path, this runs in-process as a background thread.
For the Docker path, this runs as a separate container (mcp-connector/).
"""
from __future__ import annotations

import json
import httpx
from mcp.server.fastmcp import FastMCP

_client: httpx.AsyncClient | None = None


def create_mcp_server(api_url: str = "http://localhost:8000", api_token: str = "", port: int = 3001) -> FastMCP:
    """Create and configure the MCP server with all 14 tools."""

    mcp = FastMCP("Diligence Fitness", port=port)

    async def api(method: str, path: str, **kwargs) -> dict:
        global _client
        if _client is None:
            headers = {}
            if api_token:
                headers["Authorization"] = f"Bearer {api_token}"
            _client = httpx.AsyncClient(
                base_url=api_url, timeout=30, headers=headers
            )
        resp = await getattr(_client, method)(f"/api{path}", **kwargs)
        resp.raise_for_status()
        return resp.json()

    # --- CONTEXT & STATUS (3 tools) ---

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
            "user": profile, "today": data, "rewards": rewards,
            "integrations": integrations, "active_meal_plan": meal_plan,
        }, indent=2, default=str)

    @mcp.tool()
    async def get_today(date_str: str | None = None) -> str:
        """Get today's points earned, daily gate status, breakdown by category, and activities logged. Optionally pass a date (YYYY-MM-DD)."""
        params = {"date": date_str} if date_str else {}
        data = await api("get", "/points/today", params=params)
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def get_week(start_date: str | None = None) -> str:
        """Get weekly summary including total points, active days count, target progress, and day-by-day breakdown."""
        params = {"start_date": start_date} if start_date else {}
        data = await api("get", "/points/week", params=params)
        return json.dumps(data, indent=2, default=str)

    # --- ACTIVITY LOGGING (1 tool) ---

    @mcp.tool()
    async def log_activity(
        category: str, title: str, duration_minutes: int,
        notes: str | None = None, date_str: str | None = None,
        program_day: int | None = None,
    ) -> str:
        """Log a workout or activity. Returns points earned and daily total.

        Args:
            category: Type of activity (workout, cardio, yoga, walking, cycling, swimming, other)
            title: Description of what was done
            duration_minutes: How long the activity lasted
            notes: Optional additional notes
            date_str: Optional date (YYYY-MM-DD), defaults to today
            program_day: Optional program day number
        """
        payload = {"category": category, "title": title, "duration_minutes": duration_minutes}
        if notes: payload["notes"] = notes
        if date_str: payload["date"] = date_str
        if program_day: payload["program_day"] = program_day
        data = await api("post", "/activities/log", json=payload)
        return json.dumps(data, indent=2, default=str)

    # --- FOOD & NUTRITION (2 tools) ---

    @mcp.tool()
    async def log_food(
        meal_type: str, food_name: str, calories: int | None = None,
        protein_g: float | None = None, carbs_g: float | None = None,
        fat_g: float | None = None, servings: float | None = None,
        plan_item_id: str | None = None,
    ) -> str:
        """Log a food item with optional nutrition data.

        Args:
            meal_type: One of breakfast, lunch, dinner, snack
            food_name: What was eaten
            calories: Estimated calories
            protein_g: Grams of protein
            carbs_g: Grams of carbs
            fat_g: Grams of fat
            servings: Number of servings (default 1)
            plan_item_id: Optional meal plan item ID for compliance
        """
        payload = {"meal_type": meal_type, "food_name": food_name}
        for k, v in [("calories", calories), ("protein_g", protein_g), ("carbs_g", carbs_g),
                      ("fat_g", fat_g), ("servings", servings), ("plan_item_id", plan_item_id)]:
            if v is not None: payload[k] = v
        data = await api("post", "/food/log", json=payload)
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def search_food(query: str) -> str:
        """Search for food items in Open Food Facts and USDA FoodData Central. Returns nutrition data for matching items."""
        data = await api("get", "/food/search", params={"q": query})
        return json.dumps(data, indent=2, default=str)

    # --- PROGRAMS (1 tool) ---

    @mcp.tool()
    async def get_program_schedule(date_str: str | None = None) -> str:
        """Get today's scheduled workout from the active program, including exercises with sets, reps, and weight progression."""
        params = {"date": date_str} if date_str else {}
        data = await api("get", "/programs/schedule", params=params)
        return json.dumps(data, indent=2, default=str)

    # --- REWARDS (1 tool) ---

    @mcp.tool()
    async def redeem_reward(reward_name: str) -> str:
        """Spend points on a configured reward. Returns success/failure and remaining points."""
        data = await api("post", "/points/rewards/redeem", json={"name": reward_name})
        return json.dumps(data, indent=2, default=str)

    # --- MEAL PLANS (4 tools) ---

    @mcp.tool()
    async def load_meal_plan(
        name: str, duration_days: int, meals: list[dict],
        diet_type: str | None = None, daily_calories: int | None = None,
        restrictions: list[str] | None = None,
    ) -> str:
        """Create a complete meal plan with all items.

        Args:
            name: Plan name (e.g. "7-Day Dairy-Free Keto")
            duration_days: How many days the plan covers
            meals: List of meal items with day_number, meal_type, food_name, calories, protein_g, carbs_g, fat_g
            diet_type: Optional diet type (keto, paleo, balanced, custom)
            daily_calories: Optional daily calorie target
            restrictions: Optional list of dietary restrictions
        """
        payload = {"name": name, "duration_days": duration_days, "meals": meals}
        if diet_type: payload["diet_type"] = diet_type
        if daily_calories: payload["daily_calories"] = daily_calories
        if restrictions: payload["restrictions"] = restrictions
        data = await api("post", "/meal-plans", json=payload)
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def get_meal_plan(date_str: str | None = None) -> str:
        """View the active meal plan's meals for today or a specified date."""
        data = await api("get", "/meal-plans/today")
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def update_meal_compliance(
        plan_item_id: str, status: str, substitution: str | None = None,
    ) -> str:
        """Mark a planned meal as followed, substituted, or skipped.

        Args:
            plan_item_id: The meal plan item ID
            status: One of 'followed', 'substituted', 'skipped'
            substitution: What was eaten instead (required if 'substituted')
        """
        payload = {"plan_item_id": plan_item_id, "status": status}
        if substitution: payload["substitution"] = substitution
        data = await api("post", "/meal-plans/compliance", json=payload)
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def get_plan_progress(plan_id: str | None = None) -> str:
        """Get overall compliance stats for a meal plan."""
        if plan_id:
            data = await api("get", f"/meal-plans/{plan_id}/progress")
        else:
            plans = await api("get", "/meal-plans")
            active = next((p for p in plans if p.get("status") == "active"), None)
            if not active:
                return json.dumps({"error": "No active meal plan"})
            data = await api("get", f"/meal-plans/{active['id']}/progress")
        return json.dumps(data, indent=2, default=str)

    # --- INTEGRATIONS (2 tools) ---

    @mcp.tool()
    async def configure_integration(provider: str, credentials: dict) -> str:
        """Store encrypted integration credentials. Write-only.

        Args:
            provider: Provider name (strava, polar, garmin, fitbit, usda, telegram, groq, etc.)
            credentials: Dict of credential fields
        """
        data = await api("post", "/integrations/configure", json={
            "provider": provider, "credentials": credentials,
        })
        return json.dumps(data, indent=2, default=str)

    @mcp.tool()
    async def get_integration_status() -> str:
        """Check connection status of all integration providers."""
        data = await api("get", "/integrations/status")
        return json.dumps(data, indent=2, default=str)

    return mcp
