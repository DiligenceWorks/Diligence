"""USDA FoodData Central lookup service.

Free API with 400K+ foods and research-grade nutrition data.
API key required (free, instant signup at https://fdc.nal.usda.gov/api-key-signup).
"""
from __future__ import annotations

import logging
import httpx

logger = logging.getLogger(__name__)

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"


async def search_usda(query: str, api_key: str, page_size: int = 10) -> list[dict]:
    """Search USDA FoodData Central for food items.

    Returns a list of dicts with: fdcId, description, brandName, calories,
    protein_g, carbs_g, fat_g, serving_size.
    """
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{USDA_BASE}/foods/search",
                params={
                    "api_key": api_key,
                    "query": query,
                    "pageSize": page_size,
                    "dataType": "Foundation,SR Legacy,Branded",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for food in data.get("foods", []):
            nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
            results.append({
                "fdcId": food.get("fdcId"),
                "description": food.get("description", ""),
                "brandName": food.get("brandName"),
                "source": "usda",
                "calories": nutrients.get("Energy"),
                "protein_g": nutrients.get("Protein"),
                "carbs_g": nutrients.get("Carbohydrate, by difference"),
                "fat_g": nutrients.get("Total lipid (fat)"),
                "fiber_g": nutrients.get("Fiber, total dietary"),
                "serving_size": food.get("servingSize"),
                "serving_unit": food.get("servingSizeUnit"),
            })
        return results

    except Exception as e:
        logger.warning(f"USDA search failed: {e}")
        return []
