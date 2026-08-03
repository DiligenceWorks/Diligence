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

## 2. Install Node.js

Required for Gemini CLI and Claude Desktop MCP bridge. Download the LTS version
from [nodejs.org](https://nodejs.org). Run the installer with defaults.

Verify in a **new** PowerShell window:

```powershell
node --version
```

Skip this step if you only plan to use the built-in AI Coach (see Section 7d).

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

## 6. Prepare the MCP stdio launcher

Some AI agents (Claude Desktop, ChatGPT Desktop) require stdio transport. Create the
launcher script in your Diligence-main folder:

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

## 7. Connect an AI Agent

Choose one or more of the following options. All are free.

---

### 7a. Gemini CLI (recommended free option)

**What:** Google's terminal AI agent. 1,000 free requests/day with Google sign-in.
Supports stdio and SSE MCP directly — no bridge needed.

**Requires:** Node.js (Step 2)

**Install:**

```powershell
npm install -g @google/gemini-cli
```

**First run — authenticate with Google:**

```powershell
gemini
```

Follow the browser prompt to sign in with your Google account. This is a one-time setup.

**Configure MCP:**

Create or edit the settings file:

```powershell
mkdir "$env:USERPROFILE\.gemini" -ErrorAction SilentlyContinue
$dp = ("$env:USERPROFILE\Downloads\Diligence-main") -replace '\\','\\\\'
@"
{
  "mcpServers": {
    "diligence": {
      "command": "python",
      "args": ["mcp_stdio.py"],
      "cwd": "$dp"
    }
  }
}
"@ | Set-Content "$env:USERPROFILE\.gemini\settings.json"
```

**Alternatively**, Gemini CLI supports SSE directly (unlike Claude Desktop), so you
can point it at the running MCP server without the stdio script. If your Diligence
instance has API token auth enabled (check `http://localhost:8000/agent`), include
the token in headers. Open the settings file in Notepad and paste:

```json
{
  "mcpServers": {
    "diligence": {
      "url": "http://localhost:3001/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_FROM_AGENT_PAGE"
      }
    }
  }
}
```

Omit the `headers` block if no token is shown on the Agent page.

**Use:**

1. Start Diligence in one terminal (`python -m diligence`)
2. Open a second terminal and run `gemini`
3. Type: "What's my fitness status today?"

Gemini CLI will discover the Diligence MCP tools and use them to answer.

---

### 7b. Claude Desktop (free, MCP via stdio)

**What:** Anthropic's desktop chat app. Free with a free Claude account.
Only supports stdio MCP via config file (not SSE).

**Requires:** Node.js (Step 2), free Claude account at [claude.ai](https://claude.ai)

**Install:** Download from [claude.ai/download](https://claude.ai/download) or
install from the Microsoft Store. Sign in with your free Claude account.

**Configure MCP:**

Claude Desktop reads its config from different paths depending on install method.
Set both to be safe:

Generate and save the config (this auto-resolves your Downloads path):

```powershell
$dp = ("$env:USERPROFILE\Downloads\Diligence-main") -replace '\\','\\\\'
$json = @"
{
  "mcpServers": {
    "diligence": {
      "command": "python",
      "args": ["mcp_stdio.py"],
      "cwd": "$dp"
    }
  }
}
"@

# Standard install path
mkdir "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
$json | Set-Content "$env:APPDATA\Claude\claude_desktop_config.json"

# Microsoft Store install path (set both to be safe)
$storePath = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude"
if (Test-Path $storePath) { $json | Set-Content "$storePath\claude_desktop_config.json" }
```

**Important:** Do NOT use the "Add custom connector" button in Claude Desktop's UI.
That is for remote MCP servers and may have plan restrictions. The config file
approach above is for local MCP and works on the free plan.

**Use:**

1. Start Diligence in one terminal (`python -m diligence`)
2. Quit Claude Desktop fully (right-click system tray icon > Quit)
3. Reopen Claude Desktop
4. Look for a tools/hammer icon indicating MCP is connected
5. Type: "What's my fitness status today?"

---

### 7c. ChatGPT Desktop (paid plans only)

**What:** OpenAI's desktop app. Supports local stdio MCP servers via config file.

**Requires:** ChatGPT Plus, Pro, or Team plan (not free). Developer Mode enabled.

**Install:** Download from [openai.com/chatgpt/desktop](https://openai.com/chatgpt/desktop).

**Configure MCP:**

MCP configuration is shared between ChatGPT Desktop and OpenAI Codex CLI.
The config file location may vary by version — check OpenAI's documentation
for the current path. As of mid-2026, it is typically at
`%APPDATA%\ChatGPT\chatgpt_config.json`. Use the same JSON format as
Claude Desktop (Section 7b) with your Diligence path.

**Enable Developer Mode:** Settings > Developer Mode > ON

**Use:**

1. Start Diligence in one terminal
2. Restart ChatGPT Desktop
3. Type: "What's my fitness status today?"

---

### 7d. Built-in AI Coach (simplest — no extra apps needed)

**What:** AI coaching chat built directly into the Diligence web app. No external
tools, no config files, no MCP setup. Just needs a free API key.

**Free API key providers:**

| Provider | Free tier | Get key |
|----------|-----------|---------|
| OpenRouter | 26 free models | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Groq | Fast Llama inference | [console.groq.com/keys](https://console.groq.com/keys) |
| Google AI Studio | Gemini Flash/Pro | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Hugging Face | Thousands of models | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| Ollama | Run LLMs locally, no key needed | [ollama.com](https://ollama.com/) |

**Setup:**

1. Sign up at one of the providers above and copy your API key
2. In the Diligence browser app, go to **Settings > Integrations > AI Coaching**
3. Paste your API key and select a model
4. Use the **Coach** tab in the bottom navigation

**Ollama (fully offline):**

If you want AI coaching without any internet dependency, install Ollama from
[ollama.com](https://ollama.com/), pull a model (`ollama pull llama3.1`), and
configure the Diligence AI Coaching integration to point at `http://localhost:11434`.
No API key needed.

---

## Daily Usage

Each time you want to use Diligence:

```powershell
cd "$env:USERPROFILE\Downloads\Diligence-main"
python -m diligence
```

Open `http://localhost:8000` in your browser. The app runs until you press Ctrl+C.

If using an external AI agent (Gemini CLI, Claude Desktop, ChatGPT Desktop),
make sure Diligence is running first, then open the agent.

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
| Home/Keto pages "failed to load" | Missing tzdata | `pip install tzdata` |
| "No module named diligence" | Wrong directory | `cd "$env:USERPROFILE\Downloads\Diligence-main"` |
| "No module named uvicorn" | Dependencies not installed | `pip install ".[mcp]"` |
| "No module named mcp.server.fastmcp" | Wrong MCP SDK version | `pip uninstall mcp -y && pip install "fastmcp>=3.0.0"` |
| App stops when clicking terminal | PowerShell QuickEdit | Right-click title bar > Properties > uncheck QuickEdit |
| Claude Desktop "not valid config" | Config uses `url` not `command` | Use the stdio config (Section 7b) |
| Claude Desktop "Server disconnected" | MCP extras not installed | `pip install ".[mcp]"` and check for `MCP:` line |
| Gemini CLI "no tools found" | Settings path wrong | Check `~/.gemini/settings.json` has correct `cwd` path |
| MCP line shows "not available" | Missing MCP extras | `pip install ".[mcp]"` |
