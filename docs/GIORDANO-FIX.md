# Giordano Desktop Fix — Next Session

**Date:** 2026-08-03
**Machine:** Windows, AMD Ryzen 3 2200G, 8GB RAM, user `giord`, Python 3.14
**Issue:** Claude Desktop MCP connector fails — wrong MCP package version installed

## Prerequisites

- Diligence app folder at `C:\Users\giord\Downloads\Diligence-main`
- Claude Desktop installed (Microsoft Store version)
- Node.js installed
- `mcp_stdio.py` already in the Diligence-main folder
- Claude Desktop config already set at both paths:
  - `%APPDATA%\Claude\claude_desktop_config.json`
  - `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

## Step 1 — Clean up old MCP packages

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
pip uninstall mcp mcp-cli fastmcp -y
```

## Step 2 — Fix the import in server.py

The old code imports from the wrong package. Run this once:

```powershell
(Get-Content diligence\mcp\server.py) -replace 'from mcp\.server\.fastmcp import FastMCP', 'from fastmcp import FastMCP' | Set-Content diligence\mcp\server.py
```

## Step 3 — Install the correct packages

```powershell
pip install "fastmcp>=3.0.0"
pip install tzdata
```

## Step 4 — Test the MCP stdio script

```powershell
python mcp_stdio.py
```

- **If it hangs with no output** → success. Ctrl+C to stop.
- **If it throws an error** → paste the traceback.

## Step 5 — Start Diligence

```powershell
python -m diligence
```

Confirm **both** lines appear:
- `Diligence running at http://localhost:8000`
- `MCP: http://localhost:3001/sse`

## Step 6 — Restart Claude Desktop

```powershell
Get-Process *claude* | Stop-Process -Force
```

Reopen Claude Desktop from the Start menu. Look for a tools/hammer icon indicating MCP connected.

## Step 7 — Test

In Claude Desktop, type:

> What's my fitness status today?

Claude should call the `get_context` tool and return fitness data.

Also test a write operation:

> Log a 30 minute workout called Morning Run

---

## Fallback: Built-in AI Coach (no Claude Desktop needed)

If Claude Desktop MCP continues to have issues, use the built-in coach:

1. Go to `http://localhost:8000/agent` in the browser
2. Under "Option 1 — Built-in AI Coach", click **Get key** next to **OpenRouter**
3. Sign up with Google (free, 26 free models available)
4. Copy the API key
5. In Diligence, go to **Settings > Integrations > AI Coaching**
6. Paste the key and select a model
7. Use the **Coach** tab in the bottom nav

This runs entirely inside the app — no external tools needed.

---

## Known Issues on This Machine

| Issue | Fix | Status |
|-------|-----|--------|
| tzdata not in pip dependencies | pip install tzdata manually | Pending GitHub push |
| mcp v2.0.0 removed FastMCP import | Switch to standalone fastmcp package | Fixed in subo repo, pending GitHub |
| GitHub push token expired | Need new PAT with repo scope | Not yet done |
| Migration warning: NOT NULL on point_rules.description | Non-fatal, cosmetic | Low priority |
| PowerShell QuickEdit mode pauses the app | Right-click title bar, Properties, uncheck QuickEdit | Told user |
