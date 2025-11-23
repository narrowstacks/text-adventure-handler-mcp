# Text Adventure Handler MCP

An MCP (Model Context Protocol) server that enables AI agents to run interactive text adventures with persistent game state, dice-based action resolution, and adventure-specific character stats.

## Features

- **Adventure Management**: Store multiple text adventure templates with customizable prompts
- **Game Sessions**: Track player progress across multiple parallel games
- **Dynamic Stats**: Define custom stats per adventure (e.g., D&D classes have STR/DEX/INT, sci-fi has PILOT/TECH/PERSUADE)
- **Dice System**: d20-based action resolution with stat modifiers
- **Progress Persistence**: SQLite database stores all game state and history
- **Story Generation**: Designed to work with Claude for generating story beats and outcomes
- **Flexible Actions**: Players can attempt anything; success depends on dice rolls and stat checks
- **Score Tracking**: Award points for achievements and clever solutions
- **Word Randomization**: Predefined word lists for dynamic names, locations, and items (or AI-generated alternatives)
- **Concise MCP Descriptions**: Optimized for AI context usage

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/text-adventure-handler-mcp.git
cd text-adventure-handler-mcp

# Install in development mode
pip install -e .
```

## Quick Start

### 1. Initialize the Server

```python
from adventure_handler.server import mcp, load_sample_adventures

# Load sample adventures into the database
load_sample_adventures()

# Run the MCP server
mcp.run()
```

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
Tool: start_adventure(adventure_id="fantasy_dungeon")
Returns: {
  "session_id": "uuid-string",
  "title": "The Crystal Caverns",
  "location": "Dungeon Entrance",
  "story": "Initial story text...",
  "stats": {"Strength": 10, "Dexterity": 10, ...},
  "score": 0
}
```

## MCP Tools Reference

### Core Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `list_adventures()` | View all available adventures | List of adventure metadata |
| `start_adventure(adventure_id, randomize_initial?)` | Begin a new game (optionally randomize initial content) | Session ID + initial state |
| `get_state(session_id)` | Get current game state | Full player state |
| `take_action(session_id, action, stat_name?, difficulty_class?)` | Perform an action | Success/failure + outcome |
| `roll_check(session_id, stat_name?, difficulty_class?)` | Make a stat check | Dice roll result |

### State Management

| Tool | Purpose |
|------|---------|
| `modify_stat(session_id, stat_name, value)` | Adjust stat by value |
| `update_location(session_id, location)` | Move to new location |
| `add_inventory(session_id, item)` | Add item to inventory |
| `remove_inventory(session_id, item)` | Remove item |
| `update_score(session_id, points)` | Add/subtract score |

### Information Retrieval

| Tool | Purpose |
|------|---------|
| `get_history(session_id, limit?)` | Get action history |

### Batch Operations

| Tool | Purpose |
|------|---------|
| `python_eval(session_id, code)` | Execute Python for multi-step operations |

### Word Randomization

| Tool | Purpose |
|------|---------|
| `randomize_word(session_id, word_list_name, category_name?, use_predefined?)` | Get predefined or AI-generated words |

## MCP Resources

Access game information in AI-readable formats:

- **`adventure://prompt/{adventure_id}`**: Get the adventure prompt and stat definitions
- **`session://state/{session_id}`**: Current game state as JSON
- **`session://history/{session_id}`**: Full action history as JSON

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

## Database Schema

The server uses SQLite with the following tables:

- **adventures**: Adventure templates
- **game_sessions**: Active game sessions
- **player_state**: Current player status
- **action_history**: Log of all player actions and outcomes

Database file: `adventure_handler.db` (in current directory)

## Configuration

Edit `src/adventure_handler/database.py` to change the database path:

```python
db = AdventureDB(db_path="/custom/path/adventure_handler.db")
```

## Development

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
