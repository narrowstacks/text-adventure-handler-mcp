"""Entry point for running the MCP server via uvx or command line."""
import asyncio
import argparse
import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path

# Import server/mcp only after setting up environment variables in main()
# But we can't easily do that with top-level imports unless we move them inside main
# or use importlib. However, AdventureDB reads env var at __init__.
# server.py instantiates AdventureDB at top level.
# So we MUST set env var before importing server.

def start_web_ui(open_browser=False, db_path=None):
    """Starts the Web UI using docker-compose."""
    # Locate web directory relative to this file
    base_dir = Path(__file__).resolve().parent.parent.parent
    web_dir = base_dir / "web"
    
    if not web_dir.exists():
        print(f"Warning: Web directory not found at {web_dir}. Cannot start Web UI.", file=sys.stderr)
        return

    # Determine absolute path to DB for volume mapping
    if db_path:
        host_db_path = Path(db_path).resolve()
    else:
        host_db_path = (Path.home() / ".text-adventure-handler" / "adventure_handler.db").resolve()

    # Ensure directory exists so Docker doesn't fail/create root-owned dir
    host_db_path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure file exists (touch it) so Docker maps it as file, not dir
    if not host_db_path.exists():
        try:
            host_db_path.touch()
        except Exception as e:
             print(f"Warning: Could not create DB file at {host_db_path}: {e}", file=sys.stderr)

    print(f"Starting Web UI in {web_dir}...", file=sys.stderr)
    print(f"Mapping DB: {host_db_path}", file=sys.stderr)

    env = os.environ.copy()
    env["HOST_DB_PATH"] = str(host_db_path)

    try:
        # Run docker-compose up -d --build
        subprocess.run(
            ["docker-compose", "up", "--build", "-d"], 
            cwd=str(web_dir), 
            check=True,
            stdout=sys.stderr, 
            stderr=sys.stderr,
            env=env
        )
        print("Web UI running at http://localhost:3000", file=sys.stderr)
        
        if open_browser:
            print("Opening browser...", file=sys.stderr)
            time.sleep(2) 
            webbrowser.open("http://localhost:3000")
            
    except Exception as e:
        print(f"Failed to start Web UI: {e}", file=sys.stderr)


def main():
    """Main entry point for the adventure handler MCP server."""
    parser = argparse.ArgumentParser(description="Text Adventure Handler MCP Server")
    parser.add_argument("--web-ui", action="store_true", help="Start the companion Web UI (requires Docker)")
    parser.add_argument("--open-browser", action="store_true", help="Open the Web UI in the default browser")
    parser.add_argument("--db-path", type=str, help="Path to custom SQLite database file")
    
    args, unknown = parser.parse_known_args()
    
    # Set environment variable for DB path if provided
    # This MUST happen before importing server (which inits DB)
    if args.db_path:
        os.environ["ADVENTURE_DB_PATH"] = args.db_path

    # Now import server modules
    from .server import mcp, load_sample_adventures

    if args.web_ui:
        start_web_ui(open_browser=args.open_browser, db_path=args.db_path)
    elif args.open_browser:
         webbrowser.open("http://localhost:3000")

    # Clean up sys.argv so FastMCP doesn't choke on our flags
    sys.argv = [sys.argv[0]] + unknown

    # Load sample adventures from JSON files
    asyncio.run(load_sample_adventures())

    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
