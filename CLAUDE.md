# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Text Adventure Handler MCP is a Model Context Protocol (MCP) server built with FastMCP that enables AI agents to run interactive text adventures with persistent game state, dice-based action resolution, and dynamic content generation.

**Core Architecture**: This is an MCP server, not a client application. All functionality is exposed via MCP tools and resources that external AI agents can call.

## Tools

### Context7

Use context7 tools to get information about any API or library we use (such as FastMCP)

## Development Commands

### Running the Server

```bash
# Development mode (recommended)
uv run python -m adventure_handler

# Or using the installed script
uvx text-adventure-handler-mcp

# Or from local directory
uvx --from . text-adventure-handler-mcp
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with dev dependencies
uv pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Lint and format
uv run ruff check --fix
```

### Building

```bash
# Install in development mode
uv pip install -e .

# Or with pip
pip install -e .
```

## Code Architecture

### Module Structure

- **`server.py`**: FastMCP server definition with all MCP tools and resources. Entry point for MCP functionality. Contains tool definitions decorated with `@mcp.tool()` and resource definitions with `@mcp.resource()`.
- **`__main__.py`**: Simple entry point that loads sample adventures and calls `mcp.run()`.
- **`database.py`**: SQLite database layer (`AdventureDB` class) with CRUD operations for adventures, sessions, player state, and action history.
- **`models.py`**: Pydantic models for all data structures (Adventure, GameSession, PlayerState, DiceRoll, etc.).
- **`dice.py`**: D&D-style dice rolling mechanics with advantage/disadvantage support.
- **`randomizer.py`**: Word list randomization and template substitution system for dynamic content.

### Data Flow

1. **Adventure Loading**: On startup, `load_sample_adventures()` scans `src/adventure_handler/adventures/*.json` and populates the SQLite database with adventure templates.
2. **Session Creation**: When `start_adventure()` is called, a new `GameSession` is created with initial `PlayerState` derived from the adventure's stat definitions. Players can optionally:
   - Name their character (stored in `custom_data`)
   - Roll stats using 4d6 drop lowest (D&D standard) via `roll_stats=True`
   - Provide custom stat values via `custom_stats` parameter
3. **State Persistence**: All state mutations (stats, inventory, location, score) are immediately persisted to SQLite via `db.update_player_state()`.
4. **Tool Calls**: External AI agents call MCP tools which manipulate game state and return results. The server never runs game logic automatically—it only responds to tool calls.
5. **Session Summaries**: When a play session ends, AI calls `summarize_progress()` to store a summary with key events and character changes. Later, `get_adventure_summary()` retrieves all summaries for story continuity.

### Key Patterns

**Template Substitution**: Adventures can use `{word_list_name}` or `{word_list_name.category_name}` placeholders in `initial_location` and `initial_story`. The `process_template()` function uses regex to find and replace these with random words from predefined word lists.

**Dice System**: Uses D&D 5e mechanics: `d20 + (stat_value - 10) // 2` vs Difficulty Class. Implemented in `dice.py` with `stat_check()` and `roll_check()` functions.

**Stat Modification**: The `modify_stat()` tool allows increasing or decreasing character stats during gameplay. Use positive values to increase (e.g., from training) or negative values to decrease (e.g., from drinking alcohol, exhaustion). Stats are automatically clamped to adventure-defined min/max bounds.

**Session Summaries**:
- `summarize_progress()`: Call when user ends a play session. AI provides a concise summary (2-4 sentences), list of key events, and character changes.
- `get_adventure_summary()`: Retrieves all previous summaries in chronological order, allowing AI to recap "the story so far" when continuing an adventure.

**Batch Operations**: The `python_eval()` tool allows executing arbitrary Python code with access to session state, database, and helper functions. This is for multi-step operations that would otherwise require many tool calls.

**Resource URIs**: FastMCP resources provide read-only access to adventure prompts and session data:

- `adventure://prompt/{adventure_id}` - AI-readable adventure prompt
- `session://state/{session_id}` - Current game state as JSON
- `session://history/{session_id}` - Action history as JSON
- `session://characters/{session_id}` - All characters in the session as JSON
- `session://locations/{session_id}` - All locations in the session as JSON
- `session://items/{session_id}` - All items in the session as JSON

**Dynamic Entity Creation**: AI can dynamically create new characters, locations, and items during gameplay using MCP tools:

- **Characters**: NPCs with names, descriptions, locations, optional stats, and custom properties (e.g., hostile, quest_giver)
- **Locations**: Places with descriptions, connections to other locations, and custom properties (e.g., locked, dangerous)
- **Items**: Objects with descriptions, locations (or player inventory), and custom properties (e.g., usable, consumable)

All dynamic entities are scoped to individual game sessions and stored in the database for persistence.

### Database Schema

Eight tables in SQLite (`adventure_handler.db`):

- **adventures**: Adventure templates with JSON-encoded stats and word_lists
- **game_sessions**: Session metadata (id, adventure_id, timestamps)
- **player_state**: Current state per session (location, stats, inventory, score, custom_data)
- **action_history**: Log of all actions with outcomes
- **characters**: Dynamically created NPCs (session-scoped, with stats and properties)
- **locations**: Dynamically created places (session-scoped, with connections and properties)
- **items**: Dynamically created objects (session-scoped, with location and properties)
- **session_summaries**: AI-generated summaries of play sessions with key events and character changes

JSON columns are serialized/deserialized using Pydantic models.

### Adding New Adventures

Create a JSON file in `src/adventure_handler/adventures/` following this structure:

```json
{
  "id": "unique_id",
  "title": "Adventure Title",
  "description": "Brief description",
  "prompt": "System prompt for AI to generate story",
  "stats": [
    {
      "name": "StatName",
      "description": "What this stat does",
      "default_value": 10,
      "min_value": 0,
      "max_value": 20
    }
  ],
  "word_lists": [
    {
      "name": "character_names",
      "description": "NPC names",
      "categories": {
        "hero": ["Alice", "Bob"],
        "villain": ["Evil", "Bad"]
      }
    }
  ],
  "initial_location": "{location_names.start}",
  "initial_story": "Story text with {character_names.hero} placeholder"
}
```

The server will automatically load it on startup via `load_sample_adventures()`.

## Important Implementation Details

- **FastMCP Specifics**: All tools must be decorated with `@mcp.tool()`. Resources use `@mcp.resource(uri_pattern)` and return `Resource` objects.
- **State Immutability**: Never modify session state without calling `db.update_player_state()` afterward, or changes will be lost.
- **Error Handling**: Tools return `{"error": "message"}` dictionaries rather than raising exceptions to provide graceful failures to AI agents.
- **JSON Serialization**: SQLite stores complex data as JSON strings. Always use `json.dumps()` when storing and `json.loads()` when retrieving.
- **Word List Matching**: The `get_random_word()` function returns `None` if a word list or category doesn't exist, allowing template processing to preserve the original placeholder.
