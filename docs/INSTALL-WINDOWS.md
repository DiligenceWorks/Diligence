# Diligence Fitness — Windows Installation Guide

Complete installation from a clean Windows machine with no dependencies.

---

## 1. Install Python

Download Python from [python.org/downloads](https://www.python.org/downloads/).
Use the latest **3.12** or **3.13** release (3.14 works but is bleeding edge).

**During installation, check "Add Python to PATH"** — this is critical.

Verify in a new PowerShell window:

```powershell
python --version
```

Should show `Python 3.12.x` or similar.

---

## 2. Install Node.js (required for Claude Desktop MCP)

Download the LTS version from [nodejs.org](https://nodejs.org). Run the installer with defaults.

Verify in a **new** PowerShell window:

```powershell
node --version
```

Skip this step if you only plan to use the built-in AI Coach (see Step 7b).

---

## 3. Download Diligence

Since Git is not required, download as a ZIP:

```powershell
cd "$env:USERPROFILE\Downloads"
Invoke-WebRequest -Uri "https://github.com/DiligenceWorks/Diligence/archive/refs/heads/main.zip" -OutFile Diligence.zip
Expand-Archive Diligence.zip -DestinationPath .
cd Diligence-main
```

---

## 4. Install Diligence and dependencies

Install the app with MCP support and Windows timezone data:

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
pip install ".[mcp]"
pip install tzdata
```

**Note:** The `tzdata` package is required on Windows because Python's `zoneinfo`
module has no system timezone database. Without it, the Home and Keto pages will
show "failed to load."

The `.[mcp]` extra installs the MCP server for AI agent integration. If you
only want the web app without AI features, use `pip install .` instead.

---

## 5. Start Diligence

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
python -m diligence
```

You should see:

```
Diligence running at http://localhost:8000
  Data: C:\Users\USERNAME\.diligence
  MCP:  http://localhost:3001/sse
  Press Ctrl+C to stop
```

Open `http://localhost:8000` in your browser. Create an account on the registration page.

**Important:** Do not click inside the PowerShell terminal window while the app is
running. Windows QuickEdit mode will pause the process. To prevent this permanently:
right-click the PowerShell title bar, select Properties, uncheck "QuickEdit Mode."

---

## 6. Create the MCP stdio launcher

Create the file `mcp_stdio.py` in your Diligence-main folder:

```powershell
Set-Content "$env:USERPROFILE\Downloads\Diligence-main\mcp_stdio.py" @'
from diligence.mcp.server import create_mcp_server
mcp = create_mcp_server(api_url="http://localhost:8000")
mcp.run(transport="stdio")
'@
```

Test it (Diligence must be running in another terminal):

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
python mcp_stdio.py
```

If it hangs with no output, that means success (stdio is waiting for input). Press Ctrl+C to stop.

---

## 7a. Connect Claude Desktop (free, MCP agent)

### Install Claude Desktop

Download from [claude.ai/download](https://claude.ai/download) or install from the Microsoft Store.
Sign in with a free Claude account.

### Configure MCP

Determine which install you have and set the config:

**Standard install:**

```powershell
mkdir "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
Set-Content "$env:APPDATA\Claude\claude_desktop_config.json" @'
{
  "mcpServers": {
    "diligence": {
      "command": "python",
      "args": ["mcp_stdio.py"],
      "cwd": "DILIGENCE_PATH"
    }
  }
}
'@
```

**Microsoft Store install:**

```powershell
Set-Content "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json" @'
{
  "mcpServers": {
    "diligence": {
      "command": "python",
      "args": ["mcp_stdio.py"],
      "cwd": "DILIGENCE_PATH"
    }
  }
}
'@
```

Replace `DILIGENCE_PATH` with the actual path, e.g. `C:\\Users\\giord\\Downloads\\Diligence-main`.
Note the double backslashes in JSON.

**If you are unsure which install you have**, set both configs — only the correct one will be read.

### Start and test

1. Start Diligence in a terminal (`python -m diligence`)
2. Quit Claude Desktop fully (right-click system tray icon > Quit, or `Get-Process *claude* | Stop-Process -Force`)
3. Reopen Claude Desktop
4. Look for a tools/hammer icon indicating MCP connected
5. Type: "What's my fitness status today?"

---

## 7b. Alternative: Built-in AI Coach (no extra apps needed)

If Claude Desktop MCP is not working or you prefer a simpler setup:

1. Get a free API key from one of these providers:
   - **OpenRouter** (openrouter.ai/keys) — 26 free models, sign up with Google
   - **Groq** (console.groq.com) — free tier, fast inference
   - **Google AI Studio** (aistudio.google.com) — free Gemini API key
2. In the Diligence browser app, go to **Settings > Integrations > AI Coaching**
3. Paste your API key and select a model
4. Use the **Coach** tab in the bottom navigation

---

## Daily Usage

Each time you want to use Diligence:

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
python -m diligence
```

Open `http://localhost:8000` in your browser. The app runs until you press Ctrl+C.

If using Claude Desktop, make sure Diligence is running first, then open Claude Desktop.

---

## Updating

To get the latest version:

```powershell
cd "$env:USERPROFILE\Downloads"
Remove-Item -Recurse -Force Diligence-main
Invoke-WebRequest -Uri "https://github.com/DiligenceWorks/Diligence/archive/refs/heads/main.zip" -OutFile Diligence.zip
Expand-Archive Diligence.zip -DestinationPath . -Force
cd Diligence-main
pip install ".[mcp]"
pip install tzdata
```

Your data is stored in `~\.diligence\` and is preserved across updates.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Home/Keto pages show "failed to load" | Missing tzdata | `pip install tzdata` |
| "No module named diligence" | Not in the right directory | `cd "$env:USERPROFILE\Downloads\Diligence-main"` |
| "No module named uvicorn" | Dependencies not installed | `pip install ".[mcp]"` |
| App stops when clicking terminal | PowerShell QuickEdit mode | Right-click title bar > Properties > uncheck QuickEdit |
| Claude Desktop MCP "Server disconnected" | Wrong MCP package or transport | See Step 6 for stdio setup |
| MCP "not valid configurations" | Config uses url instead of command | Use the stdio config format (Step 7a) |
| Claude Desktop MCP "not available" | MCP extras not installed | `pip install ".[mcp]"` |
