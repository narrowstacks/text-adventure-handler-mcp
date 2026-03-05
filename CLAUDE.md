# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Text Adventure Handler MCP is a Model Context Protocol (MCP) server built with FastMCP that enables AI agents to run interactive text adventures with persistent game state, dice-based action resolution, and dynamic content generation.

**Core Architecture**: This is an MCP server, not a client application. All functionality is exposed via MCP tools and resources that external AI agents can call. The server uses a narrator-driven approach where AI agents act as story narrators, managing game state through tool calls.

## Environment and Testing

- **Always use UV to test out Python files, functions, and tests.**
- **Create and use a test db, not a user's db.**
- **Python Version**: Requires Python >= 3.10 (configured in pyproject.toml)

## Tools

### Context7

Use context7 tools to get information about any API or library we use (such as FastMCP).

## Development Commands

### Running the Server

```bash
# Development mode (recommended)
uv run python -m adventure_handler

# Run with Web UI (requires Docker and local repo)
uv run python -m adventure_handler --web-ui --open-browser

# Run with custom DB path
uv run python -m adventure_handler --db-path /path/to/db.sqlite

# Or using the installed script
uvx text-adventure-handler-mcp

# Or from local directory
uvx --from . text-adventure-handler-mcp
```

### Testing

```bash
# Run all tests with UV
uv run pytest

# Run specific test file
uv run pytest tests/test_server.py

# Run with coverage
uv run pytest --cov=adventure_handler

# Run with dev dependencies
uv pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Lint and format
uv run ruff check --fix

# Check without fixing
uv run ruff check
```

### Building and Installation

```bash
# Install in development mode with UV
uv pip install -e .

# Build distribution
uv build

# Install from PyPI (when published)
pip install text-adventure-handler-mcp

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Code Architecture

### Module Structure

- **`server.py`**: FastMCP server definition with all MCP tools and resources. Entry point for MCP functionality. Contains tool definitions decorated with `@mcp.tool()` and resource definitions with `@mcp.resource()`.
- **`__main__.py`**: Simple entry point that loads sample adventures and calls `mcp.run()`.
- **`database.py`**: SQLite database layer (`AdventureDB` class) with async CRUD operations for all game entities.
- **`models.py`**: Pydantic models for all data structures (Adventure, GameSession, PlayerState, DiceRoll, Character, Location, Item, Memory, StatusEffect, Faction, etc.).
- **`dice.py`**: D&D-style dice rolling mechanics with advantage/disadvantage support.
- **`randomizer.py`**: Word list randomization and template substitution system for dynamic content.
- **`json_validator.py`**: Custom JSON validation for FastMCP tools to handle both dict and JSON string inputs.
- **`prompt_and_rules.json`**: Centralized game rules, workflow, and narrator guidelines loaded by `initial_instructions()`.

### Data Flow

1. **Initial Setup**: AI calls `initial_instructions()` to get workflow, rules, and adventure catalog.
2. **Adventure Loading**: On startup, `load_sample_adventures()` scans `src/adventure_handler/adventures/*.json` and populates the SQLite database with adventure templates.
3. **Session Creation**: When `start_adventure()` is called, a new `GameSession` is created with initial `PlayerState` derived from the adventure's stat definitions. Players can optionally:
   - Name their character (stored in `custom_data`)
   - Roll stats using 4d6 drop lowest (D&D standard) via `roll_stats=True`
   - Provide custom stat values via `custom_stats` parameter
   - Generate custom initial content via `generate_initial_content()`
4. **State Persistence**: All state mutations are immediately persisted to SQLite via async database operations.
5. **Tool Calls**: External AI agents call MCP tools which manipulate game state and return results. The server never runs game logic automatically—it only responds to tool calls.
6. **Narrator Thinking**: AI uses `narrator_thought()` to log internal planning and story tracking without exposing to users.
7. **Session Continuity**: `continue_adventure()` resumes existing sessions with full state and history.

### Key Patterns

**Template Substitution**: Adventures can use `{word_list_name}` or `{word_list_name.category_name}` placeholders in `initial_location` and `initial_story`. The `process_template()` function uses regex to find and replace these with random words from predefined word lists.

**Dice System**: Uses D&D 5e mechanics: `d20 + (stat_value - 10) // 2` vs Difficulty Class. Implemented in `dice.py` with `stat_check()` and `roll_check()` functions.

**JSON Input Validation**: Uses `JsonDict` type alias with `BeforeValidator` to automatically handle both dict and JSON string inputs in tool parameters.

**Batch Operations**: The `execute_batch()` tool allows chaining multiple tool calls without narration between them for efficiency.

**Resource URIs**: FastMCP resources provide read-only access to adventure prompts and session data:

- `adventure://prompt/{adventure_id}` - AI-readable adventure prompt
- `session://state/{session_id}` - Current game state as JSON
- `session://history/{session_id}` - Action history as JSON
- `session://characters/{session_id}` - All characters in the session as JSON
- `session://locations/{session_id}` - All locations in the session as JSON
- `session://items/{session_id}` - All items in the session as JSON

**Dynamic Entity Creation**: AI can dynamically create and manage entities during gameplay:

- **Characters**: NPCs with stats, memories, relationships
- **Locations**: Places with connections and properties
- **Items**: Objects with properties and locations
- **Status Effects**: Temporary conditions with durations
- **Factions**: Groups with reputation tracking
- **Quests**: Objectives with progress tracking

### Database Schema

Tables in SQLite (`adventure_handler.db`):

- **adventures**: Adventure templates with JSON-encoded stats and word_lists
- **game_sessions**: Session metadata (id, adventure_id, timestamps, time_of_day, day_count)
- **player_state**: Current state per session (location, stats, inventory, hp, score, custom_data, quests, status_effects, currency)
- **action_history**: Log of all actions with outcomes
- **characters**: Dynamically created NPCs (session-scoped, with stats, memories, and properties)
- **locations**: Dynamically created places (session-scoped, with connections and properties)
- **items**: Dynamically created objects (session-scoped, with location and properties)
- **session_summaries**: AI-generated summaries of play sessions with key events and character changes
- **memories**: Character memories and knowledge (linked to characters)
- **status_effects**: Active conditions affecting players or characters
- **factions**: Groups with reputation scores

JSON columns are serialized/deserialized using Pydantic models with proper validation.

### Complete Tool Reference

#### Core Workflow Tools

- **`initial_instructions()`**: Returns workflow, rules, and adventure catalog. Call FIRST.
- **`get_rules(section_name)`**: Retrieve specific rule sections for reference.
- **`narrator_thought(session_id, thought, story_status, plan, user_behavior)`**: Private narrator planning log.
- **`execute_batch(session_id, commands)`**: Chain multiple tool calls without narration.

#### Session Management

- **`list_adventures()`**: Get available adventures.
- **`list_sessions(limit)`**: List recent sessions to resume.
- **`start_adventure(adventure_id, randomize_initial, character_name, roll_stats, custom_stats, generated_story, generated_characters, generated_locations)`**: Begin new adventure.
- **`continue_adventure(session_id)`**: Resume existing session.
- **`generate_initial_content(adventure_id)`**: Generate custom opening content.

#### Information Gathering

- **`get_session_info(session_id, include_state, include_history, include_character_memories, history_limit, memory_limit, include_nearby_characters, include_available_items)`**: Consolidated info retrieval.

#### Game Actions

- **`take_action(session_id, action, stat_name, difficulty_class)`**: Log action with optional stat check.
- **`roll_check(session_id, stat_name, difficulty_class)`**: Quick d20/stat check.
- **`skill_check(session_id, action, stat_name, threshold, reason)`**: Non-roll stat check (Fallout-style). Use for dialogue, knowledge checks, or skill gates where outcome should reflect character abilities rather than chance.
- **`combat_round(session_id, target_name, attack_stat, defense_stat, weapon_damage, target_type)`**: Resolve combat turn.

#### State Management

- **`modify_state(session_id, action, value, stat_name, reason)`**: Modify HP, stats, score, or location.
- **`manage_inventory(session_id, action, item_name, quantity, properties)`**: Inventory operations (add/remove/update/check/list/use).
- **`manage_status_effect(session_id, action, effect_name, duration, description, stat_modifiers, target)`**: Handle temporary conditions.

#### Entity Management

- **`manage_character(session_id, action, name, description, location, stats, properties)`**: Create/update/delete/move NPCs.
- **`manage_location(session_id, action, name, description, connected_to, properties)`**: Create/update/delete/connect locations.
- **`manage_item(session_id, action, name, description, location, properties, quantity)`**: Create/update/delete/move items.
- **`manage_faction(session_id, action, faction_name, reputation_change, description)`**: Track group relationships.

#### Quest and Progress

- **`update_quest(session_id, quest_id, title, status, progress, objectives)`**: Manage quest objectives.
- **`manage_summary(session_id, action, summary, key_events, character_changes, summary_id)`**: Session summaries.

#### Memory and Events

- **`record_event(session_id, event_description, location, importance, tags)`**: Log public events to all witnesses.
- **`add_character_memory(session_id, character_name, description, type, importance, tags)`**: Add private character knowledge.
- **`interact_npc(session_id, npc_name, sentiment_change)`**: Adjust NPC relationships.

#### World Management

- **`manage_time(session_id, action, hours, time_of_day)`**: Advance or set in-world time.
- **`manage_economy(session_id, action, amount, item_name, quantity, price_per_unit)`**: Handle currency and trade.
- **`randomize_word(session_id, word_list_name, category_name, prompt)`**: Get random words from lists.

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
- **Async Operations**: All database operations are async using `aiosqlite`. Use `await` for all database calls.
- **State Immutability**: Never modify session state without persisting to database, or changes will be lost.
- **Error Handling**: Tools return `{"error": "message"}` dictionaries rather than raising exceptions to provide graceful failures to AI agents.
- **JSON Serialization**: SQLite stores complex data as JSON strings. Models handle serialization/deserialization automatically.
- **Input Validation**: Use `JsonDict` type for parameters that can be either dict or JSON string.
- **Word List Matching**: The `get_random_word()` function returns `None` if a word list or category doesn't exist, allowing template processing to preserve the original placeholder.

## Testing Guidelines

### Test Structure

- **`test_server.py`**: Integration tests for all MCP tools
- **`test_database.py`**: Database layer unit tests
- **`test_models.py`**: Pydantic model validation tests
- **`test_dice.py`**: Dice rolling mechanics tests
- **`test_randomizer.py`**: Word list and template tests
- **`test_memory.py`**: Memory system tests
- **`test_manage_character.py`**: Character management tests
- **`test_input_validation.py`**: JSON input validation tests

### Writing Tests

```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_tool():
    db = AdventureDB(":memory:")
    await db.init_db()
    # Test implementation

# Use fixtures for common setup
@pytest.fixture
async def session():
    db = AdventureDB(":memory:")
    await db.init_db()
    # Setup code
    return session_id
```

## Workflow Best Practices

1. **Always call `initial_instructions()` first** to understand the complete workflow and rules
2. **Use `narrator_thought()` frequently** to track story state and plan tool calls
3. **Call `record_event()` after any notable public event** to maintain NPC knowledge consistency
4. **Use `execute_batch()` for mechanical updates** when no narration is needed between tool calls
5. **Prefer consolidated tools** (`get_session_info`, `modify_state`, etc.) over individual calls
6. **Always handle tool errors gracefully** and provide appropriate narrative responses
7. **Maintain location connectivity** when creating new locations with `manage_location()`
8. **Track quest progress explicitly** with `update_quest()` rather than relying on narration

## Common Pitfalls to Avoid

- Don't modify game state through narration alone—always use appropriate tools
- Don't guess session IDs—use `list_sessions()` first
- Don't create duplicate entities—check existing ones first
- Don't skip memory logging for important events
- Don't use synchronous database operations—all are async
- Don't forget to validate JSON inputs—use `JsonDict` type
- Don't modify stats beyond their defined min/max bounds
- Don't create disconnected locations—always specify `connected_to`
