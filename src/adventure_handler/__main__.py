"""Entry point for running the MCP server via uvx or command line."""
import asyncio
import sys
import os


def main():
    """Main entry point for the adventure handler MCP server."""
    # Check for --db-path argument manually to set env var before importing server
    db_path = None
    filtered_args = [sys.argv[0]]

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--db-path" and i + 1 < len(sys.argv):
            db_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i].startswith("--db-path="):
            db_path = sys.argv[i].split("=", 1)[1]
            i += 1
        else:
            filtered_args.append(sys.argv[i])
            i += 1

    # Set environment variable for DB path if provided
    # This MUST happen before importing server (which inits DB)
    if db_path:
        os.environ["ADVENTURE_DB_PATH"] = db_path

    # Now import server modules
    from .server import mcp, load_sample_adventures

    # Clean up sys.argv so FastMCP doesn't choke on our flags
    sys.argv = filtered_args

    # Load sample adventures from JSON files
    asyncio.run(load_sample_adventures())

    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
