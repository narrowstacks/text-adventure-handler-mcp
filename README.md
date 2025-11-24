# Text Adventure Handler MCP

An MCP (Model Context Protocol) server that enables AI agents to run interactive text adventures with persistent game state, dice-based action resolution, adventure-specific character stats, and dynamic world management.

## Features

- **Adventure Management**: Store multiple text adventure templates with customizable prompts
- **Character Creation**: Players can name their character and roll stats (4d6 drop lowest) or use custom/default values
- **Game Sessions**: Track player progress across multiple parallel games
- **Dynamic Stats**: Define custom stats per adventure (e.g., D&D classes have STR/DEX/INT, sci-fi has PILOT/TECH/PERSUADE)
- **Dice System**: d20-based action resolution with stat modifiers and difficulty classes
- **Progress Persistence**: SQLite database stores all game state, history, and world changes
- **Advanced World Management**:
  - **Dynamic Entities**: Create and manage Characters, Locations, and Items on-the-fly
  - **Economy System**: Track currency, buy/sell items, and manage transactions
  - **Time Tracking**: Manage game time, day/night cycles, and time-based events
  - **Faction System**: Track reputation with different groups (Hostile to Revered)
  - **Status Effects**: Apply temporary buffs or debuffs with duration tracking
  - **Memory & Perception**: NPCs witness events and form memories that influence their behavior
- **AI Narrator Tools**:
  - **Internal Monologue**: `narrator_thought` allows the AI to plan story beats privately
  - **Batch Execution**: `execute_batch` allows performing multiple game actions in a single turn for efficiency
  - **Word Randomization**: Predefined or AI-generated word lists for dynamic names and descriptions
- **Concise MCP Descriptions**: Optimized for AI context usage
- **Web UI Dashboard**: Optional visual interface for managing adventures and game state
- **Web UI Dashboard**: Visual interface for managing adventures, sessions, and game state (optional)

## Web UI Interface

The project includes an optional web-based dashboard that provides a visual interface for managing your text adventures. The web UI runs alongside the MCP server and allows you to:

- View and manage active game sessions
- Monitor player state, inventory, and stats
- Browse adventure history and summaries
- Manage characters, locations, and items
- Track game time and faction relationships

**Note:** The Web UI requires Docker and the source code repository. It is not currently packaged with the PyPI distribution.

### Running the Web UI

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/narrowstacks/text-adventure-handler-mcp.git
    cd text-adventure-handler-mcp
    ```

2.  **Start using the helper CLI**:
    You can use the included CLI to start the Web UI and the server together (requires `uv`):

    ```bash
    uv run python -m adventure_handler --web-ui --open-browser
    ```

3.  **Or manually with Docker Compose**:
    ```bash
    cd web
    docker-compose up --build
    ```

The dashboard will be available at [http://localhost:3000](http://localhost:3000).

### Web UI Configuration

The web UI connects to the default database path: `~/.text-adventure-handler/adventure_handler.db`

If your database is located elsewhere, update the `HOST_DB_PATH` environment variable:

```bash
export HOST_DB_PATH="/path/to/your/adventure_handler.db"
cd web && docker-compose up
```

### Development Mode

For development without Docker:

```bash
# Backend (port 3001)
cd web/backend
npm install
npm run dev

# Frontend (port 5173)
cd web/frontend
npm install
npm run dev
```

## Installation

### Connecting to Claude Desktop

To use this MCP server with Claude Desktop, configure it in your settings file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### 1. Basic Configuration (Recommended)

Uses `uvx` to fetch and run the latest version automatically.

```json
{
  "mcpServers": {
    "text-adventure": {
      "command": "uvx",
      "args": ["text-adventure-handler-mcp"]
    }
  }
}
```

#### 2. Run from GitHub (Latest Version)

If you want to run the absolute latest version directly from the repository:

```json
{
  "mcpServers": {
    "text-adventure": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/narrowstacks/text-adventure-handler-mcp",
        "text-adventure-handler-mcp"
      ]
    }
  }
}
```

#### 3. Custom Database Location

If you want to store your game data in a specific location (instead of the default `~/.text-adventure-handler/`), add the `ADVENTURE_DB_PATH` environment variable:

```json
{
  "mcpServers": {
    "text-adventure": {
      "command": "uvx",
      "args": ["text-adventure-handler-mcp"],
      "env": {
        "ADVENTURE_DB_PATH": "/Users/username/my_games/adventure.db"
      }
    }
  }
}
```

#### 4. Local Development Configuration

If you have cloned the repository and want to use your local version:

```json
{
  "mcpServers": {
    "text-adventure-local": {
      "command": "uv",
      "args": ["run", "python", "-m", "adventure_handler"],
      "cwd": "/absolute/path/to/text-adventure-handler-mcp"
    }
  }
}
```

#### 5. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Quick Start

### 1. Initial Instructions

The server provides a helper tool to understand the workflow:

```
Tool: initial_instructions()
Returns: Overview of available adventures and how to start.
```

### 2. List Available Adventures

```
Tool: list_adventures()
Returns: List of adventure metadata (id, title, description)
```

### 3. Start a Game Session

```
Tool: start_adventure(
  adventure_id="fantasy_dungeon",
  character_name="Aragorn",
  roll_stats=True
)
```

## Narrator Workflow

This MCP is designed to help the AI act as a competent Game Master (GM). The recommended workflow for every turn is:

1.  **Analyze User Input**: Understand what the player wants to do.
2.  **Plan (Internal Monologue)**: Use `narrator_thought` to:
    - Check if the action follows rules.
    - Determine necessary stat checks (DC).
    - Plan story consequences.
    - Decide on tool calls.
3.  **Execute Actions**: Use `execute_batch` (or individual tools) to update the game state (move, inventory, combat, etc.).
4.  **Narrate**: Describe the outcome to the player based on the tool results.

## MCP Tools Reference

### Core Workflow

| Tool                             | Purpose                                                                     |
| :------------------------------- | :-------------------------------------------------------------------------- |
| `initial_instructions()`         | Get started guide and list of adventures.                                   |
| `get_rules(section_name?)`       | Retrieve specific rule sections (guidelines, mechanics, etc.).              |
| `narrator_thought(...)`          | **CRITICAL**: Log internal thoughts, story status, and plans before acting. |
| `execute_batch(commands)`        | **CRITICAL**: Execute multiple state-changing tools in one go.              |
| `start_adventure(...)`           | Begin a new game session.                                                   |
| `continue_adventure(session_id)` | Resume an existing session.                                                 |

### Game Mechanics

| Tool                | Purpose                                            |
| :------------------ | :------------------------------------------------- |
| `take_action(...)`  | Perform a general skill check or narrative action. |
| `combat_round(...)` | Resolve a round of combat (Player vs Enemy).       |
| `roll_check(...)`   | Make a specific stat check or raw d20 roll.        |
| `modify_state(...)` | Modify HP, stats, score, or location.              |
| `update_quest(...)` | Start, update, or complete quests.                 |

### World Management (Modular)

| Tool                        | Purpose                                                          |
| :-------------------------- | :--------------------------------------------------------------- |
| `manage_character(...)`     | Create, Read, Update, Delete, List NPCs/Characters.              |
| `manage_location(...)`      | Create, Read, Update, Delete, List Locations.                    |
| `manage_item(...)`          | Create, Read, Update, Delete, List Items in the world.           |
| `manage_faction(...)`       | Create factions and manage reputation/relationships.             |
| `manage_economy(...)`       | Handle currency, buying, selling, and item transfers.            |
| `manage_time(...)`          | Advance time, set time, or get current game time/day.            |
| `manage_status_effect(...)` | Apply, remove, or list temporary status effects (buffs/debuffs). |

### Perception & Memory

| Tool                        | Purpose                                                                                                                                               |
| :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `record_event(...)`         | Log a public event at a location. Updates witnesses' memories automatically.                                                                          |
| `add_character_memory(...)` | Implant a specific memory (rumor/secret) into an NPC.                                                                                                 |
| `interact_npc(...)`         | Simple relationship update (deprecated in favor of `manage_faction` or `record_event` for complex interactions, but still useful for simple changes). |

### State & Information (Consolidated)

| Tool                    | Purpose                                                                       |
| :---------------------- | :---------------------------------------------------------------------------- |
| `get_session_info(...)` | Get state, history, character memories, and nearby entities in a single call. |
| `manage_inventory(...)` | Add, remove, update, check, list, or use inventory items.                     |
| `manage_summary(...)`   | Create, get, or delete session summaries for long-term continuity.            |

### Content Generation

| Tool                            | Purpose                                                              |
| :------------------------------ | :------------------------------------------------------------------- |
| `randomize_word(...)`           | Get a random name/place/item from predefined lists or AI generation. |
| `generate_initial_content(...)` | Helper to generate a custom opening scenario before starting.        |

## Sample Adventures

### 1. The Crystal Caverns (`fantasy_dungeon`)

Classic fantasy dungeon crawl.

- **Stats**: Strength, Dexterity, Intelligence, Wisdom, Charisma.
- **Features**: Monsters, traps, magic, and loot.

### 2. Station Anomaly (`scifi_station`)

Deep-space horror and mystery.

- **Stats**: Piloting, Technical, Combat, Persuade.
- **Features**: Hacking, alien threats, system repairs.

### 3. The Jade Dragon Case (`noir_detective`)

Gritty urban murder mystery.

- **Stats**: Investigation, Intimidate, Sneak, Street_Smarts.
- **Features**: Interrogation, clues, moral ambiguity.

### 4. Checkout Chaos (`checkout_chaos`)

Post-apocalyptic survival comedy in a mega-mart.

- **Stats**: Scavenge, Improvisation, Diplomacy, Cart_Control.
- **Features**: Crafting weapons from junk, aisle factions, absurd corporate announcements.

### 5. Clockwork Conspiracy (`clockwork_conspiracy`)

Steampunk political intrigue.

- **Stats**: Engineering, Panache, Shadowstep, Duel.
- **Features**: Gadgets, high-society galas, rooftop chases, secret plots.

### 6. Shadows of the Cursed Shores (`cursed_shores`)

Nautical horror and piracy.

- **Stats**: Swordplay, Seamanship, Cunning, Grit.
- **Features**: Ship management, ghost crews, cursed treasure, naval combat.

### 7. The Void Claim (`void_claim`)

Sci-fi insurance investigation in a derelict ship.

- **Stats**: Investigation, Tech-Ops, Corporate Protocol, Survival.
- **Features**: Bio-horrors, corporate bureaucracy, forensic analysis.

## Creating Custom Adventures

Create a JSON file in `src/adventure_handler/adventures/`:

```json
{
  "id": "my_adventure",
  "title": "Adventure Title",
  "description": "Short description",
  "prompt": "System prompt for AI...",
  "stats": [ ... ],
  "word_lists": [ ... ],
  "initial_location": "Starting Location",
  "initial_story": "Opening narrative..."
}
```

Refer to existing JSON files for the structure of `stats`, `word_lists`, and other configuration options like `currency_config` or `time_config`.

## Unified Tool Design

The MCP tools follow a consolidated design pattern to optimize context usage and simplify the API:

### Information Gathering - `get_session_info()`

Retrieve multiple types of game information in a single call:

```python
info = get_session_info(
    session_id,
    include_state=True,              # Current location, stats, HP, inventory
    include_history=True,             # Recent action history
    include_character_memories="Merchant",  # NPC memories
    include_nearby_characters=True,   # Characters at current location
    include_available_items=True,     # Items at current location
    history_limit=10,
    memory_limit=10
)
```

### Inventory Management - `manage_inventory()`

All inventory operations through a single tool:

```python
# Add item
manage_inventory(session_id, action="add", item_name="Sword", quantity=1)

# Remove item
manage_inventory(session_id, action="remove", item_name="Potion")

# Check if item exists
manage_inventory(session_id, action="check", item_name="Key")

# List all inventory
manage_inventory(session_id, action="list")

# Use/consume item
manage_inventory(session_id, action="use", item_name="Healing Potion")

# Update item properties
manage_inventory(session_id, action="update", item_name="Sword",
                 properties={"enchanted": True})
```

### Session Summaries - `manage_summary()`

Create and retrieve story summaries for long-term continuity:

```python
# Create summary when ending a play session
manage_summary(session_id, action="create",
               summary="Player defeated the dragon...",
               key_events=["Found magic sword", "Met wizard"],
               character_changes=["Gained confidence", "Lost innocence"])

# Get all summaries to recap the story
manage_summary(session_id, action="get")

# Get only the latest summary
manage_summary(session_id, action="get_latest")

# Delete a specific summary
manage_summary(session_id, action="delete", summary_id="abc123")
```

### State Modifications - `modify_state()`

All player state changes through action-based API:

```python
# Heal/damage HP
modify_state(session_id, action="hp", value=-10, reason="Fell down stairs")

# Modify stats (temporary or permanent changes)
modify_state(session_id, action="stat", stat_name="Dexterity", value=-1)

# Award/deduct points
modify_state(session_id, action="score", value=100)

# Move to new location
modify_state(session_id, action="location", value="Hospital")
```

## License

MIT License - See LICENSE file for details
