# Diligence Content Compendium — Bibliography & Source Index

**Compiled:** 2026-07-19
**Repo:** `subo.littlefake.com/scot/fitness-rewards`
**Path:** `data/seed/`

---

## Exercise Data Sources

### 1. hasaneyldrm/exercises-dataset

- **URL:** https://github.com/hasaneyldrm/exercises-dataset
- **License:** MIT (exercise data — names, categories, body parts, equipment, targets, muscle groups, multilingual instructions)
- **Media license:** Gym Visual proprietary — GIFs/images removed from repo (Jun 2026) due to conflicting ownership claims. `media_id` references retained but point to no bundled assets. Separate license required from https://gymvisual.com/ for any visual media use.
- **Version:** Commit `225b17d` (data-only, post-media-removal)
- **Records:** 1,324 exercises
- **Languages:** English, Spanish, Italian, Turkish, Russian, Chinese, Hindi, Polish, Korean, French
- **Fields used:** id, name, category, body_part, equipment, instructions (dict by language), instruction_steps, muscle_group, secondary_muscles, target, media_id
- **Attribution:** Dataset created for the LogPress app. Per NOTICE.md, exercise data is MIT; any media use requires Gym Visual attribution (© Gym Visual — https://gymvisual.com/) and compliance with their Terms & Conditions.
- **Stars:** ~15.7K (Jul 2026)
- **Provenance note:** Co-authored commits with Claude Opus 4.8 visible in git history. Data appears derived from ExerciseDB / exercisedb.io with Gym Visual media, restructured and translated.

### 2. yuhonas/free-exercise-db

- **URL:** https://github.com/yuhonas/free-exercise-db
- **License:** Unlicense (public domain)
- **Records:** 873 exercises
- **Languages:** English only
- **Fields used:** name, force (push/pull/static), level (beginner/intermediate/expert), mechanic (compound/isolation), equipment, primaryMuscles, secondaryMuscles, instructions (array of steps), category, images, id
- **Attribution:** Originally derived from exercises.json. Public domain, no attribution required.
- **Images:** 873 exercises have image references (relative paths like `Exercise_Name/0.jpg`, `Exercise_Name/1.jpg`). Images are bundled in the repo under `exercises/` — static position photos, not animated GIFs.
- **Provenance note:** Community-maintained. Exercises stored as individual JSON files in `exercises/` directory.

### 3. Unified exercise library (compiled)

- **File:** `data/seed/unified-exercise-library.json`
- **Records:** 2,079 unique exercises
- **Composition:** 1,206 unique to hasaneyldrm + 761 unique to free-exercise-db + 112 merged from both
- **Merge logic:** Name-matched (case-insensitive). Overlapping exercises enriched with force/level/mechanic from free-exercise-db and multilingual instructions from hasaneyldrm. Equipment and body part terms normalized to a controlled vocabulary. Deterministic UUIDs generated from source+id hash.
- **Index file:** `data/seed/exercise-index.json` — grouped by body_part, equipment, and category for fast lookup.

---

## Food & Nutrition Data Sources

### 4. USDA FoodData Central — Foundation Foods

- **URL:** https://fdc.nal.usda.gov/download-datasets
- **Download:** `FoodData_Central_foundation_food_json_2026-04-30.zip`
- **License:** U.S. Government work, public domain (no copyright)
- **Records:** 363 foods (after filtering 32 null entries from 395 total)
- **Release date:** April 30, 2026
- **Description:** Lab-analyzed nutrient profiles for commonly consumed foods. Highest-quality USDA data — each food has analytically determined values from multiple samples across different locations and time periods.
- **Fields used:** fdcId, description, foodCategory, foodNutrients (per-nutrient: name, amount, unitName), foodPortions (portionDescription, gramWeight), publicationDate
- **Nutrients extracted:** 22 key nutrients per food (calories, protein, fat, carbs, fiber, sugar, sodium, calcium, iron, magnesium, potassium, zinc, vitamins A/C/D/B12, folate, saturated/mono/polyunsaturated fat, cholesterol, water)
- **Citation:** U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2026. fdc.nal.usda.gov.

### 5. USDA FoodData Central — SR Legacy

- **URL:** https://fdc.nal.usda.gov/download-datasets
- **Download:** `FoodData_Central_sr_legacy_food_json_2018-04.zip`
- **License:** U.S. Government work, public domain (no copyright)
- **Records:** 7,793 foods
- **Release date:** April 2018 (final release of the Standard Reference database)
- **Description:** The USDA National Nutrient Database for Standard Reference, Legacy Release. Comprehensive nutrient data for ~8,000 food items. Superseded by Foundation Foods and FNDDS for new analyses but remains the most complete single-file whole-food reference.
- **Categories (25):** Beef Products (954), Vegetables (814), Baked Products (518), Lamb/Veal/Game (464), Poultry (383), Beverages (366), Sweets (358), Fruits (355), Baby Foods (345), Pork (336), Fast Foods (312), Dairy/Egg (291), Legumes (290), Finfish/Shellfish (264), Soups/Sauces (254), Fats/Oils (216), Breakfast Cereals (195), Cereal Grains/Pasta (181), Snacks (176), Sausages/Luncheon Meats (167), American Indian/Alaska Native Foods (165), Nuts/Seeds (137), Restaurant Foods (109), Meals/Entrees/Sides (81), Spices/Herbs (63)
- **Citation:** U.S. Department of Agriculture, Agricultural Research Service. USDA National Nutrient Database for Standard Reference, Legacy Release. Available at fdc.nal.usda.gov.

### 6. Unified food library (compiled)

- **File:** `data/seed/unified-food-library.json`
- **Records:** 8,068 foods
- **Composition:** 363 from Foundation Foods (priority) + 7,705 from SR Legacy (gap-fill). Foundation Foods take precedence when both datasets contain the same food.
- **Lifestyle pattern tagging:** Each food tagged with applicable eating patterns based on category membership and keyword matching. Patterns: Mediterranean, DASH, Blue Zones, plant-based, anti-inflammatory, keto. Keto tag additionally filtered by carbs ≤ 10g/100g.
- **Nutrient completeness:** calories 96%, protein 99%, fat 99%, carbs 99%, fiber 90%
- **Index file:** `data/seed/food-index.json` — grouped by USDA category and lifestyle pattern.

---

## Lifestyle Content Sources (Crawled)

The following were crawled 2026-07-19 using ttp-crawler on subo for lifestyle eating framing and pattern descriptions. Stored in `/home/claude/diligence-content/food/crawled/` (not in git — reference material for future content generation).

### 7. Harvard T.H. Chan School of Public Health — The Nutrition Source

- **URLs:**
  - https://nutritionsource.hsph.harvard.edu/healthy-eating-plate/
  - https://nutritionsource.hsph.harvard.edu/what-should-you-eat/
- **Content:** Healthy Eating Plate guidelines, food group recommendations, evidence-based eating guidance
- **Quality:** Full content retrieved (38KB + 7KB)
- **License:** Educational/research use. Content © The President and Fellows of Harvard College.
- **Use:** Reference for lifestyle pattern descriptions and evidence-based food group framing.

### 8. Harvard Health Publishing

- **URLs:**
  - https://www.health.harvard.edu/staying-healthy/mindful-eating
  - https://www.health.harvard.edu/staying-healthy/foods-that-fight-inflammation
- **Content:** Mindful eating practices, anti-inflammatory food lists and principles
- **Quality:** Full articles retrieved (13KB each)
- **License:** Content © Harvard Health Publishing. Reference use only.
- **Use:** Framing eating as mindfulness practice; anti-inflammatory pattern food lists.

### 9. National Heart, Lung, and Blood Institute (NHLBI)

- **URL:** https://www.nhlbi.nih.gov/education/dash-eating-plan
- **Content:** DASH Eating Plan overview — food groups, serving sizes, principles
- **Quality:** Good overview retrieved (4KB)
- **License:** U.S. Government work, public domain
- **Use:** DASH pattern definition and food group serving guidance.

### 10. NutritionFacts.org

- **URL:** https://nutritionfacts.org/topics/plant-based-diets/
- **Content:** Plant-based diet research summaries, topic index with 74 linked posts
- **Quality:** Rich content (27KB)
- **License:** Content by Michael Greger, M.D. Reference use only.
- **Use:** Plant-based pattern evidence base and food recommendations.

### 11. Blue Zones (Dan Buettner / Blue Zones LLC)

- **URLs attempted:** https://www.bluezones.com/recipes/food-guidelines/ (blocked — 403)
- **Content recovered via web search:** Blue Zones food guidelines, 11 principles, longevity diet pillars (plant slant, beans as cornerstone, hara hachi bu, whole grains, seasonal vegetables)
- **Key sources found:**
  - Blue Zones Food Guidelines page (blocked but content indexed by search engines)
  - NPR: "Eating To Break 100: Longevity Diet Tips From The Blue Zones" (Apr 2015)
  - NASM: "The Blue Zone Diet: What to Eat to Live Longer"
  - News-Medical.net: "The Principles of the Blue Zone Diet" (Feb 2024)
- **Reference:** Buettner, D. (2012). The Blue Zones: 9 Lessons for Living Longer. National Geographic. Buettner, D. & Skemp, S. (2016). Blue Zones: Lessons From the World's Longest Lived. American Journal of Lifestyle Medicine, 10(5), 318-321.
- **Use:** Blue Zones pattern definition and food recommendations.

### 12. Oldways Preservation Trust

- **URLs:**
  - https://oldwayspt.org/traditional-diets/mediterranean-diet
  - https://oldwayspt.org/traditional-diets/asian-diet
  - https://oldwayspt.org/traditional-diets/african-heritage-diet
- **Content:** Traditional diet pyramid descriptions (thin — JS-heavy site returned minimal text)
- **Quality:** Limited (40-69 words per page via curl)
- **License:** Content © Oldways Preservation Trust. Reference use only.
- **Use:** Mediterranean, Asian Heritage, and African Heritage diet pattern framing. Would benefit from manual review or Playwright crawl for full content.

---

## Sources Considered but Not Included

| Source | Reason |
|--------|--------|
| Nutrola Open Food Nutrition Dataset (500K+ foods, CC BY-SA 4.0) | GitHub repo `nutrola/open-food-nutrition-dataset` returned 404. May be private or renamed. Worth revisiting — would add branded food data. |
| OpenNutrition (300K+ foods, TSV) | Download endpoint returned HTML, not data file. API may require auth or different URL. |
| Open Food Facts (4M+ products) | Already integrated in Diligence via API (search_food MCP tool). Bulk download available at https://world.openfoodfacts.org/data but 8GB+ compressed — too large for seed data. |
| Google Nutrition5k (5,006 dishes, CC 4.0) | Visual/ML research dataset — dish photos with nutrition. Useful for future image-based food logging, not for seed library. |
| USDA FNDDS (Food and Nutrient Database for Dietary Studies) | 64MB JSON — survey-oriented, maps to What We Eat In America. Useful for meal composition research but too specialized for seed data. |
| USDA Branded Foods (3.1GB) | 400K+ branded products. Too large for seed; better served by live API (USDA FoodData Central API or Open Food Facts). |
| ExRx.net exercise database | Copyrighted. Excellent reference for exercise technique but not redistributable. |
| ACE (American Council on Exercise) exercise library | Copyrighted. Professional reference, not open data. |
| NSCA exercise database | Copyrighted. Academic/professional use, not open data. |

---

## Licensing Summary

| Source | License | Redistribution | Attribution required |
|--------|---------|---------------|---------------------|
| hasaneyldrm exercise data | MIT | ✅ Yes | MIT notice |
| hasaneyldrm exercise media | Gym Visual proprietary | ❌ Separate license needed | © Gym Visual |
| free-exercise-db | Unlicense (public domain) | ✅ Yes | None |
| USDA Foundation Foods | U.S. Gov't public domain | ✅ Yes | Courtesy citation |
| USDA SR Legacy | U.S. Gov't public domain | ✅ Yes | Courtesy citation |
| Harvard content | © Harvard | ❌ Reference only | Full citation |
| NHLBI content | U.S. Gov't public domain | ✅ Yes | Courtesy citation |
| NutritionFacts.org content | © Michael Greger | ❌ Reference only | Full citation |
| Blue Zones content | © Blue Zones LLC | ❌ Reference only | Full citation |

**Bottom line:** The compiled exercise library (MIT + public domain data) and food library (USDA public domain) are fully redistributable under MIT/public domain terms. The crawled lifestyle content is reference material for generating original descriptions — not for direct reproduction.
