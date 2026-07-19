# Diligence Content Compendium — Inventory

**Generated:** 2026-07-19
**Purpose:** Pre-loaded content for the Diligence fitness + lifestyle app
**Location:** `/home/claude/diligence-content/` on subo

---

## Exercise Library

**Path:** `exercises/`
**Status:** ✅ COMPILED — ready for integration

### Datasets merged
| Source | License | Exercises | Languages | Unique fields |
|--------|---------|-----------|-----------|---------------|
| hasaneyldrm/exercises-dataset | MIT | 1,324 | 10 (en, es, it, tr, ru, zh, hi, pl, ko, fr) | muscle_group, media_id |
| yuhonas/free-exercise-db | Public domain | 873 | 1 (en) | force, level, mechanic |

### Unified library
- **File:** `exercises/unified-exercise-library.json` (2,079 exercises)
- **Index:** `exercises/exercise-index.json` (grouped by body_part, equipment, category)
- Overlap: 112 exercises (enriched from both sources)
- Unique from hasaneyldrm: 1,206
- Unique from free-exercise-db: 761

### Schema per exercise
```json
{
  "id": "UUID (deterministic from source+id)",
  "source_id": "original ID",
  "sources": ["hasaneyldrm", "free-exercise-db"],
  "name": "3/4 Sit-Up",
  "slug": "3-4-sit-up",
  "category": "strength|cardio|flexibility|plyometrics",
  "body_part": "core|legs|arms|back|chest|shoulders|neck|cardio",
  "equipment": "bodyweight|dumbbell|barbell|cable|machine|...",
  "target_muscle": "abs",
  "secondary_muscles": ["hip flexors"],
  "force": "push|pull|static",
  "level": "beginner|intermediate|expert",
  "mechanic": "compound|isolation",
  "instructions": {"en": ["step 1", "step 2"], "es": [...], ...},
  "tips": null,
  "media_id": "0001"
}
```

### Coverage
| Dimension | Count |
|-----------|-------|
| Strength | 1,871 |
| Flexibility | 105 |
| Plyometrics | 60 |
| Cardio | 43 |
| Bodyweight | 411 |
| Dumbbell | 403 |
| Barbell | 306 |
| Beginner-tagged | 523 |
| Intermediate-tagged | 293 |
| Expert-tagged | 57 |

### Media status
The hasaneyldrm dataset originally included GIFs from Gym Visual, but they were removed due to ownership disputes. The data now ships with `media_id` references only. Options for media:
1. License from Gym Visual directly (commercial use)
2. Generate descriptions + prompt-based illustrations
3. Link to YouTube/free video demonstrations
4. Community-contributed (user-uploaded form videos)

---

## Food & Lifestyle Library

**Path:** `food/`
**Status:** ✅ COMPILED — ready for integration

### USDA Foundation Foods (Apr 2026)
- **File:** `food/usda-foundation/` — 363 foods, detailed nutrient profiles
- Source: USDA FoodData Central, public domain
- Very high quality, lab-verified nutrients

### USDA SR Legacy (Apr 2018)
- **File:** `food/usda-sr-legacy/` — 7,793 foods, comprehensive categories
- Source: USDA FoodData Central, public domain
- Complete USDA reference dataset for whole/common foods

### Unified food library
- **File:** `food/unified-food-library.json` (8,068 foods)
- **Index:** `food/food-index.json` (grouped by category + lifestyle pattern)
- 25 USDA categories, 99% nutrient completeness for macros

### Lifestyle pattern tags
Each food is tagged with applicable eating patterns — framed as lifestyle choices, not diets:

| Pattern | Foods tagged | Philosophy |
|---------|-------------|------------|
| DASH | 4,252 (52%) | Heart health through balanced whole foods |
| Mediterranean | 3,127 (38%) | Traditional regional eating, olive oil, seafood, plants |
| Keto | 2,455 (30%) | Low-carb, high-fat whole foods |
| Blue Zones | 2,210 (27%) | Longevity-focused: beans, greens, whole grains |
| Plant-based | 2,102 (26%) | Whole food, plant-forward eating |
| Anti-inflammatory | 1,909 (23%) | Foods that reduce chronic inflammation |
| Untagged | 2,341 (29%) | General foods, processed items, baby foods |

### Crawled lifestyle content
**Path:** `food/crawled/` — evidence-based content from health sources

| Source | Topic | Quality |
|--------|-------|---------|
| Harvard T.H. Chan | Healthy Eating Plate | ✅ Full content (38KB) |
| Harvard T.H. Chan | What Should I Eat? | ✅ Good overview (7KB) |
| Harvard Health | Mindful Eating | ✅ Full article (13KB) |
| Harvard Health | Anti-inflammatory Foods | ✅ Full article (13KB) |
| NutritionFacts.org | Plant-Based Diets | ✅ Rich content (27KB) |
| NHLBI | DASH Eating Plan | ✅ Good overview (4KB) |
| Blue Zones (web search) | Food Guidelines | ✅ Via search results |
| Oldways | Mediterranean/Asian/African Heritage | ⚠️ Thin (JS-heavy site) |

### Nutrients per 100g (schema)
```json
{
  "calories": 160,
  "protein_g": 2.0,
  "fat_g": 14.7,
  "carbs_g": 8.5,
  "fiber_g": 6.7,
  "sugar_g": 0.7,
  "sodium_mg": 7,
  "calcium_mg": 12,
  "iron_mg": 0.6,
  "potassium_mg": 485,
  "vitamin_c_mg": 10,
  "saturated_fat_g": 2.1,
  "cholesterol_mg": 0
}
```

---

## Integration Plan (Proposed)

### Phase 1: Exercise Library
1. Add `ExerciseLibrary` model to Diligence (new table)
2. Migration script to load unified-exercise-library.json
3. New MCP tool: `search_exercises(query, body_part?, equipment?, level?)`
4. Frontend: exercise browser with category/equipment filters
5. Link exercises to activity logging (select from library, not free-text)

### Phase 2: Food Library
1. Add `FoodLibrary` model (or extend existing FoodLog with lookup)
2. Migration to load unified-food-library.json
3. Lifestyle pattern browsing: "Show me Mediterranean foods"
4. New MCP tool: `browse_foods(pattern?, category?)`
5. Frontend: lifestyle pattern explorer (not calorie counter)

### Phase 3: Lifestyle Patterns
1. Curated pattern guides (from crawled content + search data)
2. "What's your eating style?" onboarding question
3. Pattern-aware meal suggestions
4. Seasonal food recommendations
5. Multi-language support (exercise instructions already in 10 languages)

---

## Files on disk

```
/home/claude/diligence-content/
├── INVENTORY.md                          ← this file
├── exercises/
│   ├── exercises-dataset.json            ← raw hasaneyldrm (17MB)
│   ├── exercises-schema.json             ← schema
│   ├── free-exercise-db/                 ← raw yuhonas (873 files)
│   ├── unified-exercise-library.json     ← MERGED (2,079 exercises)
│   ├── exercise-index.json               ← lookup index
│   ├── analyze.py                        ← analysis script
│   └── merge.py                          ← merge script
├── food/
│   ├── usda-foundation/                  ← USDA Foundation (363 foods)
│   ├── usda-sr-legacy/                   ← USDA SR Legacy (7,793 foods)
│   ├── unified-food-library.json         ← MERGED (8,068 foods)
│   ├── food-index.json                   ← lookup index
│   ├── build-food-library.py             ← build script
│   └── crawled/                          ← lifestyle content (18 files)
```
