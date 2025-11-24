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

## Installation

### Connecting to Claude Desktop

To use this MCP server with Claude Desktop, you need to configure it in your Claude settings:

#### 1. Locate Your Configuration File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### 2. Add Server Configuration

**Option A: Using uvx (Recommended - no installation needed)**

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

**Option B: Run from local directory (for development)**

```json
{
  "mcpServers": {
    "text-adventure": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/text-adventure-handler-mcp",
        "text-adventure-handler-mcp"
      ]
    }
  }
}
```

**Option C: Run from GitHub (latest version)**

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

#### 3. Restart Claude Desktop

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
| `modify_hp(...)`    | Heal or damage the player.                         |
| `modify_stat(...)`  | Permanently increase/decrease a player stat.       |
| `update_score(...)` | Award points for achievements.                     |
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

| Tool                       | Purpose                                                                                                   |
| :------------------------- | :-------------------------------------------------------------------------------------------------------- |
| `get_session_info(...)`    | **Consolidated tool**: Get state, history, character memories, nearby entities. Replaces 3 separate tools. |
| `manage_inventory(...)`    | **Consolidated tool**: Add, remove, update, check, list, or use inventory items.                          |
| `manage_summary(...)`      | **Consolidated tool**: Create, get, or delete session summaries for long-term continuity.                 |

**Note:** The following tools have been replaced by consolidated versions:
- `get_state()` → `get_session_info(include_state=True)`
- `get_history()` → `get_session_info(include_history=True)`
- `get_character_memories()` → `get_session_info(include_character_memories="name")`
- `add_inventory()` → `manage_inventory(action="add")`
- `remove_inventory()` → `manage_inventory(action="remove")`
- `summarize_progress()` → `manage_summary(action="create")`
- `get_adventure_summary()` → `manage_summary(action="get")`

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

## Tool Consolidation & Context Optimization

To reduce context consumption in MCP clients, several commonly-used tools have been consolidated into unified APIs:

### Why Consolidation?

Each MCP tool consumes context in AI agents. By consolidating related operations into single tools with action parameters, we:
- **Reduce tool count** from 36 to 32 (11% reduction)
- **Enable multi-operation queries** (e.g., get state + history in one call)
- **Add new functionality** without increasing tool count
- **Maintain backward compatibility** through clear migration paths

### Consolidated Tools

#### `get_session_info()` - All Information Gathering

Replaces 3 separate tools: `get_state()`, `get_history()`, `get_character_memories()`

**Example:**
```python
# Old way (3 separate tool calls):
state = get_state(session_id)
history = get_history(session_id, limit=10)
memories = get_character_memories(session_id, "Merchant")

# New way (1 tool call):
info = get_session_info(
    session_id,
    include_state=True,
    include_history=True,
    include_character_memories="Merchant",
    history_limit=10
)
```

#### `manage_inventory()` - All Inventory Operations

Replaces 2 tools and adds 4 new operations: `add_inventory()`, `remove_inventory()` + `update`, `check`, `list`, `use`

**Actions:** `add`, `remove`, `update`, `check`, `list`, `use`

#### `manage_summary()` - Session Summary Management

Replaces 2 tools and adds 2 new operations: `summarize_progress()`, `get_adventure_summary()` + `get_latest`, `delete`

**Actions:** `create`, `get`, `get_latest`, `delete`

### Migration Guide

See the [CLAUDE.md](CLAUDE.md#consolidated-tools-context-optimization) file for detailed migration examples and code patterns.

## License

MIT License - See LICENSE file for details
