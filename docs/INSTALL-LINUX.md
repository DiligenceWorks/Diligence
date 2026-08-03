# Diligence Fitness — Linux Installation Guide

Complete installation from a clean Linux machine with no dependencies.
Tested on Ubuntu 22.04+, Debian 12+. Most steps work on any distro with
Python 3.10+ and pip.

---

## 1. Install Python and pip

Most Linux distributions include Python 3. Verify:

```bash
python3 --version
pip3 --version
```

If pip is missing:

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install python3-pip python3-venv unzip curl

# Fedora
sudo dnf install python3-pip python3 unzip curl

# Arch
sudo pacman -S python-pip python unzip curl
```

---

## 2. Install Node.js

Required for Gemini CLI. Skip if you only plan to use the built-in AI Coach
(see Section 7d).

```bash
# Debian/Ubuntu (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Fedora
sudo dnf install nodejs

# Arch
sudo pacman -S nodejs npm

# Or via nvm (any distro)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install --lts
```

Verify:

```bash
node --version
npm --version
```

---

## 3. Download Diligence

```bash
cd ~/Downloads
curl -L -o Diligence.zip https://github.com/DiligenceWorks/Diligence/archive/refs/heads/main.zip
unzip Diligence.zip
cd Diligence-main
```

Or with git (if installed):

```bash
cd ~/Downloads
git clone https://github.com/DiligenceWorks/Diligence.git Diligence-main
cd Diligence-main
```

---

## 4. Install Diligence and dependencies

**Option A — System-wide (simpler):**

```bash
cd ~/Downloads/Diligence-main
pip3 install ".[mcp]" --break-system-packages
```

The `--break-system-packages` flag is required on Ubuntu 23.04+ and Debian 12+
due to PEP 668 (externally managed environments). It is safe for user-level
installs.

**Option B — Virtual environment (cleaner):**

```bash
cd ~/Downloads/Diligence-main
python3 -m venv .venv
source .venv/bin/activate
pip install ".[mcp]"
```

If using a venv, you must activate it (`source .venv/bin/activate`) each time
before running Diligence.

**Note:** Unlike Windows, Linux does not need the `tzdata` pip package. The
system timezone database at `/usr/share/zoneinfo/` is used automatically.

---

## 5. Start Diligence

```bash
cd ~/Downloads/Diligence-main
python3 -m diligence
```

You should see:

```
Diligence running at http://localhost:8000
  Data: /home/USERNAME/.diligence
  MCP:  http://localhost:3001/sse
  Press Ctrl+C to stop
```

Open `http://localhost:8000` in your browser. Create an account on the
registration page.

To run in the background:

```bash
nohup python3 -m diligence > diligence.log 2>&1 &
```

---

## 6. Prepare the MCP stdio launcher

Some AI agents (Claude Desktop) require stdio transport. Create the launcher:

```bash
cat > ~/Downloads/Diligence-main/mcp_stdio.py << 'EOF'
from diligence.mcp.server import create_mcp_server
mcp = create_mcp_server(api_url="http://localhost:8000")
mcp.run(transport="stdio")
EOF
```

Test it (Diligence must be running in another terminal):

```bash
cd ~/Downloads/Diligence-main
python3 mcp_stdio.py
```

If it hangs with no output, that is success (stdio waiting for input). Ctrl+C to stop.

---

## 7. Connect an AI Agent

Choose one or more of the following options. All are free.

---

### 7a. Gemini CLI (recommended free option)

**What:** Google's terminal AI agent. 1,000 free requests/day with Google sign-in.
Supports stdio and SSE MCP directly — no bridge needed.

**Requires:** Node.js (Step 2)

**Install:**

```bash
npm install -g @google/gemini-cli
```

**First run — authenticate with Google:**

```bash
gemini
```

Follow the browser prompt to sign in with your Google account. One-time setup.

**Configure MCP:**

Gemini CLI supports SSE directly, so you can point it straight at the running
MCP server — no stdio script needed:

```bash
mkdir -p ~/.gemini
cat > ~/.gemini/settings.json << 'EOF'
{
  "mcpServers": {
    "diligence": {
      "url": "http://localhost:3001/sse"
    }
  }
}
EOF
```

Alternatively, use the stdio launcher:

```json
{
  "mcpServers": {
    "diligence": {
      "command": "python3",
      "args": ["mcp_stdio.py"],
      "cwd": "/home/USERNAME/Downloads/Diligence-main"
    }
  }
}
```

Replace `USERNAME` with your actual username.

**Use:**

1. Start Diligence in one terminal (`python3 -m diligence`)
2. Open a second terminal and run `gemini`
3. Type: "What's my fitness status today?"

Gemini CLI will discover the Diligence MCP tools and use them to answer.

---

### 7b. Claude Desktop (free, Debian/Ubuntu only — beta)

**What:** Anthropic's desktop app. Free with a free Claude account.
Official Linux beta released July 9, 2026. Debian/Ubuntu only.

**Requires:** Ubuntu 22.04+ or Debian 12+, free Claude account

**Install:**

```bash
sudo curl -fsSLo /usr/share/keyrings/claude-desktop-archive-keyring.asc \
  https://downloads.claude.ai/claude-desktop/key.asc

echo "deb [signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc] \
  https://downloads.claude.ai/claude-desktop/apt/stable stable main" \
  | sudo tee /etc/apt/sources.list.d/claude-desktop.list

sudo apt update && sudo apt install claude-desktop
```

For Fedora, Arch, or other distros, see the community package at
[github.com/aaddrick/claude-desktop-debian](https://github.com/aaddrick/claude-desktop-debian).

**Configure MCP:**

```bash
mkdir -p ~/.config/Claude
cat > ~/.config/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "diligence": {
      "command": "python3",
      "args": ["mcp_stdio.py"],
      "cwd": "/home/USERNAME/Downloads/Diligence-main"
    }
  }
}
EOF
```

Replace `USERNAME` with your actual username.

If using a virtual environment, use the full path to the venv Python:

```json
{
  "mcpServers": {
    "diligence": {
      "command": "/home/USERNAME/Downloads/Diligence-main/.venv/bin/python",
      "args": ["mcp_stdio.py"],
      "cwd": "/home/USERNAME/Downloads/Diligence-main"
    }
  }
}
```

**Use:**

1. Start Diligence in a terminal (`python3 -m diligence`)
2. Quit and reopen Claude Desktop
3. Look for a tools/hammer icon indicating MCP is connected
4. Type: "What's my fitness status today?"

---

### 7c. ChatGPT Desktop (not available on Linux)

OpenAI has not released an official ChatGPT Desktop app for Linux as of
August 2026. A sign-up page exists for future availability. Community wrappers
(lencx/ChatGPT, Snap packages) do not support MCP.

If you have a ChatGPT paid plan, you can use the **Codex CLI** instead:

```bash
npm install -g @openai/codex
```

Codex CLI shares MCP configuration and supports stdio servers. Requires a
ChatGPT Plus, Pro, or Team plan.

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

If you want AI coaching without any internet dependency:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
```

Then configure Diligence AI Coaching to point at `http://localhost:11434`.
No API key needed.

---

## Daily Usage

Each time you want to use Diligence:

```bash
cd ~/Downloads/Diligence-main
python3 -m diligence
```

If using a venv:

```bash
cd ~/Downloads/Diligence-main
source .venv/bin/activate
python3 -m diligence
```

Open `http://localhost:8000` in your browser. The app runs until you press Ctrl+C.

If using an external AI agent (Gemini CLI, Claude Desktop), make sure Diligence
is running first, then open the agent.

---

## Optional: Run as a systemd service

To start Diligence automatically on boot:

```bash
sudo tee /etc/systemd/system/diligence.service << EOF
[Unit]
Description=Diligence Fitness
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Downloads/Diligence-main
ExecStart=$(which python3) -m diligence
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now diligence
```

Check status:

```bash
sudo systemctl status diligence
journalctl -u diligence -f
```

---

## Updating

```bash
cd ~/Downloads
rm -rf Diligence-main
curl -L -o Diligence.zip https://github.com/DiligenceWorks/Diligence/archive/refs/heads/main.zip
unzip Diligence.zip
cd Diligence-main
pip3 install ".[mcp]" --break-system-packages
```

Or with git:

```bash
cd ~/Downloads/Diligence-main
git pull origin main
pip3 install ".[mcp]" --break-system-packages
```

Your data is stored in `~/.diligence/` and is preserved across updates.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "No module named diligence" | Wrong directory or venv not active | `cd ~/Downloads/Diligence-main` and `source .venv/bin/activate` if using venv |
| "No module named uvicorn" | Dependencies not installed | `pip3 install ".[mcp]" --break-system-packages` |
| "No module named mcp.server.fastmcp" | Wrong MCP SDK version | `pip3 uninstall mcp -y && pip3 install "fastmcp>=3.0.0" --break-system-packages` |
| "externally-managed-environment" | PEP 668 on Ubuntu 23.04+ | Add `--break-system-packages` or use a venv |
| MCP line shows "not available" | Missing MCP extras | `pip3 install ".[mcp]" --break-system-packages` |
| Claude Desktop MCP not loading | Wrong config path | Check `~/.config/Claude/claude_desktop_config.json` exists |
| Gemini CLI "no tools found" | Settings path wrong | Check `~/.gemini/settings.json` has correct `cwd` path |
| Port 8000 already in use | Another service on that port | `python3 -m diligence --port 8080` or stop the conflicting service |
