"""Diligence CLI — run the fitness app from the command line."""
from __future__ import annotations

import argparse
import os
import sys
import secrets
import webbrowser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="diligence",
        description="Diligence — self-hosted fitness rewards platform",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to run on (default: 8000)",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Don't open the browser automatically",
    )
    parser.add_argument(
        "--no-mcp", action="store_true",
        help="Disable the MCP connector",
    )
    parser.add_argument(
        "--data-dir", type=str, default=None,
        help="Data directory (default: ~/.diligence)",
    )

    args = parser.parse_args()

    # Set up data directory
    data_dir = Path(args.data_dir) if args.data_dir else Path.home() / ".diligence"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Auto-generate secrets on first run
    env_file = data_dir / ".env"
    if not env_file.exists():
        secret_key = secrets.token_hex(32)
        api_token = secrets.token_hex(32)
        env_file.write_text(
            f"SECRET_KEY={secret_key}\n"
            f"API_TOKEN={api_token}\n"
            f"BASE_URL=http://localhost:{args.port}\n"
            f"DATA_DIR={data_dir}\n"
        )
        print(f"Created config at {env_file}")
        print(f"MCP token: {api_token}")

    # Point pydantic-settings at the env file
    os.environ.setdefault("DATA_DIR", str(data_dir))

    # Load existing env file
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    if args.no_mcp:
        os.environ["MCP_ENABLED"] = "false"

    # Open browser after a short delay
    url = f"http://localhost:{args.port}"
    if not args.no_browser:
        import threading

        def _open():
            import time
            time.sleep(2)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    print(f"\n  Diligence running at {url}")
    print(f"  Data: {data_dir}")
    print(f"  Press Ctrl+C to stop\n")

    # Run uvicorn
    import uvicorn
    uvicorn.run(
        "diligence.main:app",
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
