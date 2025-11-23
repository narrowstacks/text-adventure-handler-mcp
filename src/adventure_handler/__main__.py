"""Entry point for running the MCP server via uvx or command line."""
from .server import mcp, load_sample_adventures


def main():
    """Main entry point for the adventure handler MCP server."""
    # Load sample adventures from JSON files
    load_sample_adventures()

    # Run the FastMCP server
    mcp.run()


if __name__ == "__main__":
    main()
