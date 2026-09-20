
  DILIGENCE
  Self-hosted fitness rewards platform
  =====================================

  QUICK START (Windows)
  ---------------------
  1. Extract this entire folder to your Desktop or Documents
  2. Double-click  start.bat
  3. Your browser opens to http://localhost:8000
  4. Create your account on first visit

  That's it. No installation needed.


  YOUR DATA
  ---------
  Everything is stored in the "data" folder right here:
    - data/data.db    — your database (workouts, points, rewards)
    - data/.env       — your configuration (auto-generated)

  Your data never leaves your computer.
  To back up, just copy the "data" folder somewhere safe.
  To move to another computer, copy this entire Diligence folder.


  STOPPING
  --------
  Press Ctrl+C in the black command window, or just close it.


  AI AGENT CONNECTION (Optional)
  ------------------------------
  Diligence includes an MCP connector for AI agents like Claude Desktop.
  After starting, the MCP endpoint is at:
    URL:    http://localhost:3001/sse
    Token:  (see data/.env, the API_TOKEN line)

  Claude Desktop config (claude_desktop_config.json):
    {
      "mcpServers": {
        "diligence": {
          "url": "http://localhost:3001/sse",
          "headers": {
            "Authorization": "Bearer YOUR_API_TOKEN_HERE"
          }
        }
      }
    }


  SYSTEM REQUIREMENTS
  -------------------
  - Windows 10 or later (64-bit)
  - 150 MB disk space
  - 300 MB free RAM
  - Any web browser (Edge, Chrome, Firefox)
  - No admin rights needed
  - No internet needed (except for Strava/Polar sync)


  TROUBLESHOOTING
  ---------------
  "Windows protected your PC" (SmartScreen):
    Click "More info" then "Run anyway". This appears because the
    app is not digitally signed, not because it is harmful.

  "Port already in use":
    Another program is using port 8000. Close it, or run:
      start.bat --port 9000

  The window closes immediately:
    Open a Command Prompt, navigate to this folder, and type:
      start.bat
    to see the error message.


  LICENSE
  -------
  MIT License — DiligenceWorks Pte. Ltd.
  https://github.com/DiligenceWorks/Diligence

