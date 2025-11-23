# Text Adventure Handler MCP

An MCP (Model Context Protocol) server that enables AI agents to run interactive text adventures with persistent game state, dice-based action resolution, and adventure-specific character stats.

## Features

- **Adventure Management**: Store multiple text adventure templates with customizable prompts
- **Character Creation**: Players can name their character and roll stats (4d6 drop lowest) or use custom/default values
- **Game Sessions**: Track player progress across multiple parallel games
- **Dynamic Stats**: Define custom stats per adventure (e.g., D&D classes have STR/DEX/INT, sci-fi has PILOT/TECH/PERSUADE)
- **Stat Modification**: Characters' stats can be increased or decreased during play based on story events (e.g., drinking alcohol decreases Intelligence)
- **Session Summaries**: AI-generated summaries of play sessions with key events and character changes for story continuity
- **Dice System**: d20-based action resolution with stat modifiers
- **Progress Persistence**: SQLite database stores all game state and history
- **Story Generation**: Designed to work with Claude for generating story beats and outcomes
- **Flexible Actions**: Players can attempt anything; success depends on dice rolls and stat checks
- **Score Tracking**: Award points for achievements and clever solutions
- **Word Randomization**: Predefined word lists for dynamic names, locations, and items (or AI-generated alternatives)
- **Dynamic Entity Creation**: AI can create new characters, locations, and items on-the-fly during gameplay
- **Concise MCP Descriptions**: Optimized for AI context usage

## Installation

### Connecting to Claude Desktop

To use this MCP server with Claude Desktop, you need to configure it in your Claude settings:

#### 1. Locate Your Configuration File

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Or use Claude Desktop's built-in editor:

1. Open Claude Desktop Settings (system menu bar)
2. Navigate to **Developer** tab
3. Click **Edit Config**

#### 2. Add Server Configuration

**Option A: Using uvx (Recommended - no installation needed)**

Add this to your `claude_desktop_config.json`:

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

**Option D: Traditional Python installation**

First install the package:

```bash
# Clone the repository
git clone https://github.com/narrowstacks/text-adventure-handler-mcp.git
cd text-adventure-handler-mcp

# Install with pip
pip install -e .
```

Then configure Claude:

```json
{
  "mcpServers": {
    "text-adventure": {
      "command": "text-adventure-handler-mcp"
    }
  }
}
```

#### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

#### 4. Verify Connection

Look for the MCP server indicator in the bottom-right corner of Claude Desktop. You should see "text-adventure" listed as a connected server.

#### Troubleshooting

If the server doesn't connect:

1. **Check logs**:

   - **macOS/Linux**: `~/Library/Logs/Claude/mcp*.log`
   - **Windows**: `%APPDATA%\Claude\logs`

2. **Test the server manually**:

   ```bash
   uvx text-adventure-handler-mcp
   ```

3. **Verify uv/uvx is installed**:
   ```bash
   uvx --version
   ```
   If not installed, follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

### Standalone Usage (Without Claude Desktop)

You can also run the server standalone for testing or use with other MCP clients:

```bash
# Using uvx (no installation needed)
uvx text-adventure-handler-mcp

# Or from local directory
uvx --from . text-adventure-handler-mcp

# Or if installed traditionally
text-adventure-handler-mcp
```

## Quick Start

### 1. Run the Server

The server automatically loads sample adventures on startup:

```bash
# Using UV
uvx text-adventure-handler-mcp

# Or if installed traditionally
text-adventure-handler-mcp
```

The server will:

- Load sample adventures from JSON files
- Initialize the SQLite database
- Start the MCP server ready to accept connections

### 2. List Available Adventures

```
Tool: list_adventures()
Returns: [
  {"id": "fantasy_dungeon", "title": "The Crystal Caverns", "description": "..."},
  {"id": "scifi_station", "title": "Station Anomaly", "description": "..."},
  {"id": "noir_detective", "title": "The Jade Dragon Case", "description": "..."}
]
```

### 3. Start a Game Session

```
Tool: start_adventure(
  adventure_id="fantasy_dungeon",
  character_name="Aragorn",  # Optional: name your character
  roll_stats=True  # Optional: roll stats with 4d6 drop lowest
)
Returns: {
  "session_id": "uuid-string",
  "title": "The Crystal Caverns",
  "location": "Dungeon Entrance",
  "story": "Initial story text...",
  "stats": {"Strength": 14, "Dexterity": 12, ...},  # Rolled stats
  "score": 0,
  "character_name": "Aragorn"
}
```

## MCP Tools Reference

### Core Tools

| Tool                                                                                             | Purpose                                                | Returns                        |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------ |
| `list_adventures()`                                                                              | View all available adventures                          | List of adventure metadata     |
| `start_adventure(adventure_id, randomize_initial?, character_name?, roll_stats?, custom_stats?)` | Begin a new game with optional character customization | Session ID + initial state     |
| `continue_adventure(session_id)`                                                                 | Resume an existing adventure                           | Current state + recent history |
| `get_state(session_id)`                                                                          | Get current game state                                 | Full player state              |
| `take_action(session_id, action, stat_name?, difficulty_class?)`                                 | Perform an action                                      | Success/failure + outcome      |
| `roll_check(session_id, stat_name?, difficulty_class?)`                                          | Make a stat check                                      | Dice roll result               |

### State Management

| Tool                                         | Purpose                                                 |
| -------------------------------------------- | ------------------------------------------------------- |
| `modify_stat(session_id, stat_name, change)` | Increase/decrease stat by amount (positive or negative) |
| `move_to_location(session_id, location)`     | Move to new location                                    |
| `add_inventory(session_id, item)`            | Add item to inventory                                   |
| `remove_inventory(session_id, item)`         | Remove item                                             |
| `update_score(session_id, points)`           | Add/subtract score                                      |

### Session Continuity

| Tool                                                                       | Purpose                                     |
| -------------------------------------------------------------------------- | ------------------------------------------- |
| `summarize_progress(session_id, summary, key_events?, character_changes?)` | Create session summary for story continuity |
| `get_adventure_summary(session_id)`                                        | Get all summaries to recap the story so far |

### Dynamic Entity Creation

| Tool                                                                                  | Purpose                        |
| ------------------------------------------------------------------------------------- | ------------------------------ |
| `create_character(session_id, name, description, location, stats?, properties?)`      | Create a new NPC/character     |
| `list_characters(session_id, location?)`                                              | List all characters in session |
| `get_character(character_id)`                                                         | Get character details          |
| `update_character(character_id, name?, description?, location?, stats?, properties?)` | Update character properties    |
| `create_location(session_id, name, description, connected_to?, properties?)`          | Create a new location          |
| `list_locations(session_id)`                                                          | List all locations in session  |
| `get_location(location_id)`                                                           | Get location details           |
| `update_location(location_id, name?, description?, connected_to?, properties?)`       | Update location properties     |
| `create_item(session_id, name, description, location?, properties?)`                  | Create a new item              |
| `list_items(session_id, location?)`                                                   | List all items in session      |
| `get_item(item_id)`                                                                   | Get item details               |
| `update_item(item_id, name?, description?, location?, properties?)`                   | Update item properties         |

### Information Retrieval

| Tool                              | Purpose            |
| --------------------------------- | ------------------ |
| `get_history(session_id, limit?)` | Get action history |

### Batch Operations

| Tool                            | Purpose                                  |
| ------------------------------- | ---------------------------------------- |
| `python_eval(session_id, code)` | Execute Python for multi-step operations |

### Word Randomization

| Tool                                                                          | Purpose                              |
| ----------------------------------------------------------------------------- | ------------------------------------ |
| `randomize_word(session_id, word_list_name, category_name?, use_predefined?)` | Get predefined or AI-generated words |

## MCP Resources

Access game information in AI-readable formats:

- **`adventure://prompt/{adventure_id}`**: Get the adventure prompt and stat definitions
- **`session://state/{session_id}`**: Current game state as JSON
- **`session://history/{session_id}`**: Full action history as JSON
- **`session://characters/{session_id}`**: All characters in the session as JSON
- **`session://locations/{session_id}`**: All locations in the session as JSON
- **`session://items/{session_id}`**: All items in the session as JSON

## Sample Adventures

### 1. The Crystal Caverns (fantasy_dungeon)

Explore a magical dungeon in search of the Crystal of Power.

**Stats**: Strength, Dexterity, Intelligence, Wisdom, Charisma

**Features**:

- Environmental puzzles and challenges
- Combat encounters with monsters
- Treasure discovery and loot
- Magic system integration

### 2. Station Anomaly (scifi_station)

Investigate mysterious events on a deep-space research station.

**Stats**: Piloting, Technical, Combat, Persuade

**Features**:

- System hacking and repairs
- Alien encounters
- Crew interaction and mystery
- Time pressure and resource management

### 3. The Jade Dragon Case (noir_detective)

Solve a murder mystery in a gritty urban setting.

**Stats**: Investigation, Intimidate, Sneak, Street_Smarts

**Features**:

- Crime scene investigation
- Suspect interrogation
- Red herrings and twists
- Moral ambiguity

## Dice Rolling System

The system uses **d20 + modifier** resolution:

```
Roll = d20 (1-20) + Stat Modifier
Stat Modifier = (Stat Value - 10) / 2, rounded down

Success = Roll >= Difficulty Class (DC)
```

**Difficulty Classes**:

- DC 10: Easy
- DC 12: Medium
- DC 15: Hard
- DC 18: Very Hard
- DC 20: Nearly Impossible

## Creating Custom Adventures

### Method 1: JSON File

Create a JSON file in `src/adventure_handler/adventures/`:

```json
{
  "id": "my_adventure",
  "title": "Adventure Title",
  "description": "Short description",
  "prompt": "System prompt for AI...",
  "stats": [
    {
      "name": "Stat Name",
      "description": "What this stat represents",
      "default_value": 10,
      "min_value": 0,
      "max_value": 20
    }
  ],
  "initial_location": "Starting Location",
  "initial_story": "Opening narrative..."
}
```

### Method 2: Programmatically

```python
from adventure_handler.models import Adventure, StatDefinition
from adventure_handler.server import db

# Create stats
stats = [
    StatDefinition(name="Stat1", description="...", default_value=10),
    StatDefinition(name="Stat2", description="...", default_value=10),
]

# Create adventure
adventure = Adventure(
    id="unique_id",
    title="Title",
    description="Description",
    prompt="AI prompt...",
    stats=stats,
    initial_location="Start",
    initial_story="Story...",
)

# Save to database
db.add_adventure(adventure)
```

## Workflow Example: Using with Claude

```
User: "Let's play the Crystal Caverns adventure"

Claude calls: start_adventure("fantasy_dungeon")
Claude reads: adventure://prompt/fantasy_dungeon (gets detailed prompt)

Claude: "You enter the dungeon. Three paths diverge before you.
         Path A: Dark and narrow (requires Perception check)
         Path B: Well-lit but suspicious (may be trapped)
         Path C: Mysterious glow in distance (draws you forward)
         What do you do?"

User: "I try to climb the cavern wall to scout ahead"

Claude calls: take_action(session_id, "Climb cavern wall", stat_name="Dexterity", difficulty_class=14)
Claude receives: success=false, roll_message="Rolled 8, DC 14"

Claude: "Your fingers slip on the damp stone. You manage to climb about 8 feet before
         gravity wins. You tumble down, taking damage and landing with a painful thud.
         You've learned that direct climbing isn't viable here."

Claude calls: update_score(session_id, -5) # Penalty for failure
Claude calls: get_state(session_id) # Check updated state

... adventure continues with meaningful consequences for player choices
```

## Batch Operations with `python_eval()`

For complex multi-step operations, use `python_eval()` to execute Python code directly. This is more efficient than multiple tool calls:

```python
code = """
# Multi-step quest completion sequence
if state.score < 100:
    _result = "Not enough experience yet"
else:
    state.location = "Dragon's Lair"
    state.inventory.append("Ancient Sword")
    state.stats["Strength"] += 2
    state.score += 250
    _result = {
        "quest": "completed",
        "reward": "Ancient Sword",
        "new_level": state.stats["Strength"]
    }
"""

result = python_eval(session_id, code)
```

**Available in `python_eval()` scope:**

- `session` - GameSession object
- `state` - PlayerState (alias for session.state)
- `db` - Database instance
- `stat_check(value, dc)` - Perform stat check
- `roll_check(dc)` - Roll d20

**Return values:**

- Assign to `_result` variable to return data
- State changes automatically persist to database
- Response includes updated game state

## Word Randomization for Dynamic Content

Each adventure defines **predefined word lists** with categorized words for names, locations, and items. Use the `randomize_word()` tool to either:

1. Get a random predefined word (consistent within adventure)
2. Request an AI-generated word (fresh and unique each time)

### Word List Structure

Adventures define words as categorized lists in their JSON:

```json
{
  "word_lists": [
    {
      "name": "character_names",
      "description": "NPC names for encounters",
      "categories": {
        "dwarf": ["Thorin", "Gimli", "Durin"],
        "elf": ["Legolas", "Elrond", "Tauriel"],
        "human": ["Aragorn", "Boromir", "Éowyn"]
      }
    },
    {
      "name": "location_names",
      "description": "Room and area names",
      "categories": {
        "chamber": ["Hall of Shadows", "Vault of Whispers"],
        "passage": ["Spiral Staircase", "Grand Hallway"]
      }
    }
  ]
}
```

### Usage Examples

**Get a random predefined elf name:**

```python
result = randomize_word(
    session_id=session_id,
    word_list_name="character_names",
    category_name="elf",
    use_predefined=True
)
# Returns: {"source": "predefined", "word": "Legolas", "word_list": "character_names", "category": "elf"}
```

**Get an AI-generated location:**

```python
result = randomize_word(
    session_id=session_id,
    word_list_name="location_names",
    category_name="chamber",
    use_predefined=False
)
# Returns: {"source": "ai_generated", "prompt": "Generate a unique chamber name for a Fantasy Dungeon. Return only the word/name, no explanation.", ...}
```

**Get any random item name:**

```python
result = randomize_word(
    session_id=session_id,
    word_list_name="item_names",
    use_predefined=True
)
# Returns: random word from any category in item_names
```

### Built-in Word Lists

Each sample adventure includes predefined word lists:

**Fantasy Dungeon (fantasy_dungeon):**

- `character_names`: dwarf, elf, human, goblin
- `location_names`: chamber, passage, danger_zone
- `item_names`: weapon, armor, artifact

**Station Anomaly (scifi_station):**

- `character_names`: human_crew, alien, android
- `location_names`: sector, facility, danger_zone
- `item_names`: weapon, tech, artifact

**The Jade Dragon Case (noir_detective):**

- `character_names`: suspect, detective, underworld
- `location_names`: crime_scene, establishment, safe_place
- `item_names`: evidence, weapon, clue

### Creating Custom Word Lists

When creating custom adventures, include word lists in your JSON:

```json
{
  "id": "my_adventure",
  "word_lists": [
    {
      "name": "npc_names",
      "description": "Names for NPCs",
      "categories": {
        "friendly": ["Alice", "Bob", "Charlie"],
        "hostile": ["Villain", "Tyrant", "Lord"]
      }
    }
  ]
}
```

## Template Substitution in Initial Content

Adventures can use **template syntax** in their `initial_location` and `initial_story` to automatically substitute random words from word lists when a session starts. This creates unique opening narratives without requiring the AI to generate content.

### Template Syntax

Use curly braces with word list references:

- `{word_list_name}` - Pick a random word from any category
- `{word_list_name.category_name}` - Pick from a specific category

### How It Works

When `start_adventure()` is called with `randomize_initial=True` (default):

1. All placeholders in initial_location are replaced with random words
2. All placeholders in initial_story are replaced with random words
3. The processed location is stored in the session state
4. The processed story is returned to the caller

### Examples

**Fantasy Dungeon:**

```
initial_location: "{location_names.chamber}"
→ Could become: "Hall of Shadows" or "Vault of Whispers"

initial_story: "...A trap set by {character_names}..."
→ Could become: "...A trap set by Legolas..." or "...A trap set by Boromir..."
```

**Station Anomaly:**

```
initial_location: "{location_names.facility}"
→ Could become: "Medical Bay" or "Science Lab"

initial_story: "...{character_names.alien} in {location_names.danger_zone}..."
→ Could become: "...Zyx'theta in Reactor Core..." or "...Krell-7 in Radiation Sector..."
```

### Controlling Randomization

**Enable template substitution (default):**

```
start_adventure(adventure_id="fantasy_dungeon", randomize_initial=True)
```

**Disable template substitution (return raw templates):**

```
start_adventure(adventure_id="fantasy_dungeon", randomize_initial=False)
# Returns: location="{location_names.chamber}", story with {placeholders}
```

When disabled, the raw template strings are returned, allowing the AI to handle substitution or generate custom content instead.

### Creating Adventures with Templates

When defining initial_location and initial_story in your JSON:

```json
{
  "id": "my_adventure",
  "word_lists": [
    {
      "name": "npcs",
      "description": "NPC names",
      "categories": {
        "ally": ["Alice", "Bob"],
        "enemy": ["Villain", "Tyrant"]
      }
    }
  ],
  "initial_location": "{npcs.ally}'s Tavern",
  "initial_story": "You arrive at the tavern to find {npcs.ally} nervously waiting. Word has it {npcs.enemy} is hunting them. The stakes have never been higher."
}
```

This adventure will generate a unique opening every time a session starts, with actual NPC names substituted into the narrative.

## Dynamic Entity Creation

The AI can dynamically create new NPCs, locations, and items during gameplay to enrich the story. These entities are persisted to the database and scoped to individual game sessions.

### Characters (NPCs)

Create characters with stats and properties:

```python
create_character(
    session_id="abc123",
    name="Mysterious Merchant",
    description="An old merchant with knowing eyes",
    location="Town Square",
    stats={"Wisdom": 15, "Charisma": 12},  # Optional
    properties={"friendly": True, "quest_giver": True}  # Optional
)
```

### Locations

Create new areas with connections to other places:

```python
create_location(
    session_id="abc123",
    name="Hidden Cellar",
    description="A dusty cellar filled with ancient wine bottles",
    connected_to=["Tavern", "Secret Tunnel"],  # Optional
    properties={"locked": False, "discovered": True}  # Optional
)
```

### Items

Create items that can be placed in the world or inventory:

```python
create_item(
    session_id="abc123",
    name="Ancient Key",
    description="A rusty iron key with strange runes",
    location="Hidden Cellar",  # Or None for player inventory
    properties={"usable": True, "quest_item": True}  # Optional
)
```

### Use Cases

- AI encounters a situation requiring a new NPC and creates them on the spot
- Story requires a new location not in the original adventure template
- Player finds a unique item the AI invents based on narrative needs
- Dynamic quest creation with custom characters and objectives

All created entities are:

- Persisted to the database
- Accessible via list/get/update tools
- Session-specific (won't affect other games)
- Available through resource URIs for quick reference

## Database Schema

The server uses SQLite with the following tables:

- **adventures**: Adventure templates
- **game_sessions**: Active game sessions
- **player_state**: Current player status (including character name in custom_data)
- **action_history**: Log of all player actions and outcomes
- **characters**: Dynamically created NPCs (session-scoped)
- **locations**: Dynamically created places (session-scoped)
- **items**: Dynamically created objects (session-scoped)
- **session_summaries**: AI-generated summaries of play sessions with key events and character changes

Database file: `adventure_handler.db` (in current directory)

## Configuration

Edit `src/adventure_handler/database.py` to change the database path:

```python
db = AdventureDB(db_path="/custom/path/adventure_handler.db")
```

## Development

### Using UV

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run ruff check --fix

# Run server in development mode
uv run python -m adventure_handler
```

### Using pip

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff check --fix
```

## Architecture Notes

- **Context Efficiency**: All MCP descriptions are concise to minimize token usage
- **Stat Flexibility**: Each adventure defines its own stats, allowing varied gameplay styles
- **Improv Support**: Players can attempt anything; stat checks determine success
- **Batch Operations**: Tools are designed to support multi-step operations via LLM orchestration
- **Persistent State**: All game data persists in SQLite for long-running campaigns

## License

MIT License - See LICENSE file for details
