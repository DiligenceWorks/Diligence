from __future__ import annotations

"""Open Food Facts API client for barcode scanning and food search."""
import httpx
from app.schemas.food import FoodSearchResult

OFF_BASE = "https://world.openfoodfacts.org"
USER_AGENT = "FitnessRewards/1.0 (fitness.littlefake.com)"


async def lookup_barcode(barcode: str) -> FoodSearchResult | None:
    """Lookup a product by barcode from Open Food Facts."""
    url = f"{OFF_BASE}/api/v2/product/{barcode}.json"
    params = {"fields": "product_name,brands,nutriments,serving_size,image_front_small_url"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200:
            return None
        data = resp.json()

    if data.get("status") != 1 or "product" not in data:
        return None

    p = data["product"]
    n = p.get("nutriments", {})

    return FoodSearchResult(
        barcode=barcode,
        product_name=p.get("product_name"),
        brand=p.get("brands"),
        calories_100g=n.get("energy-kcal_100g"),
        protein_100g=n.get("proteins_100g"),
        carbs_100g=n.get("carbohydrates_100g"),
        fat_100g=n.get("fat_100g"),
        fiber_100g=n.get("fiber_100g"),
        sugar_100g=n.get("sugars_100g"),
        serving_size=p.get("serving_size"),
        image_url=p.get("image_front_small_url"),
    )


async def search_food(query: str, page: int = 1) -> list[FoodSearchResult]:
    """Search for food products by name."""
    url = f"{OFF_BASE}/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10,
        "page": page,
        "fields": "code,product_name,brands,nutriments,serving_size,image_front_small_url",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for p in data.get("products", []):
        n = p.get("nutriments", {})
        results.append(FoodSearchResult(
            barcode=p.get("code"),
            product_name=p.get("product_name"),
            brand=p.get("brands"),
            calories_100g=n.get("energy-kcal_100g"),
            protein_100g=n.get("proteins_100g"),
            carbs_100g=n.get("carbohydrates_100g"),
            fat_100g=n.get("fat_100g"),
            fiber_100g=n.get("fiber_100g"),
            sugar_100g=n.get("sugars_100g"),
            serving_size=p.get("serving_size"),
            image_url=p.get("image_front_small_url"),
        ))
    return results
