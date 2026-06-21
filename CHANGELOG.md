# Changelog

All notable changes to Diligence are documented here.

## [1.0.0] — 2026-06-18

Initial open-source release.

### Features
- Points economy with daily gate, weekly targets, weekly reset
- Science-based onboarding (PAR-Q+, TTM, BREQ-2 motivation profiling)
- Activity logging (manual + Strava OAuth + Polar OAuth sync)
- Food logging with Open Food Facts barcode scanning + USDA FoodData Central
- 90-day structured program tracking
- Configurable reward shop
- In-app support chat with Telegram notifications
- 14-tool MCP connector for AI agent integration
- Meal plan system with compliance tracking
- Dynamic integration configuration (11 providers)
- B2A discovery layer (llms.txt, agent-card.json, SKILL.md)

### Security
- Fernet-encrypted credential storage (HKDF key derivation)
- Signed JWT OAuth state parameters
- MCP connector authentication via API_TOKEN
- First-user auto-admin grant
- Traceback suppression in error responses
