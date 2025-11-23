"""FastMCP server for text adventure handler."""
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import Resource

from .database import AdventureDB
from .models import Adventure, StatDefinition, WordList, Character, Location, Item, InventoryItem, QuestStatus, Memory
from .dice import stat_check
from .dice import roll_check as dice_roll_check
from .randomizer import get_random_word, generate_word_prompt, process_template

# Initialize FastMCP server
mcp = FastMCP("Text Adventure Handler MCP")
db = AdventureDB()

@mcp.tool()
async def initial_instructions() -> dict:
    """
    Get instructions for starting a text adventure session.
    Call this tool first to understand the workflow and available options.
    """
    await db.init_db()  # Ensure DB is ready
    adventures = await db.list_adventures()

    # Load instructions from JSON file
    file_path = Path(__file__).parent / "prompt_and_rules.json"
    if not file_path.exists():
        return {"error": "prompt_and_rules.json not found"}

    with open(file_path, "r", encoding="utf-8") as f:
        instructions = json.load(f)

    # Add available adventures dynamically
    instructions["available_adventures"] = adventures

    return instructions



@mcp.tool()
async def get_rules(section_name: str = None) -> dict:
    """
    Get specific sections or all eligible sections of the adventure rules and guidelines.
    Excludes sections like 'welcome', 'drop_context', 'workflow', and 'features'.

    Args:
        section_name: (Optional) The name of the specific section to retrieve (e.g., "guidelines_and_rules").
                      If not provided, all eligible sections will be returned.
    """
    file_path = Path(__file__).parent / "prompt_and_rules.json"
    if not file_path.exists():
        return {"error": "prompt_and_rules.json not found"}

    with open(file_path, "r", encoding="utf-8") as f:
        all_rules = json.load(f)

    excluded_sections = ["welcome", "drop_context", "workflow", "features", "available_adventures"] # Also exclude available_adventures

    if section_name:
        if section_name in excluded_sections:
            return {"error": f"Section '{section_name}' is not accessible via this tool."}
        if section_name in all_rules:
            return {section_name: all_rules[section_name]}
        else:
            return {"error": f"Section '{section_name}' not found."}
    else:
        eligible_rules = {k: v for k, v in all_rules.items() if k not in excluded_sections}
        return eligible_rules

@mcp.tool()
async def narrator_thought(
    session_id: str,
    thought: str,
    story_status: str,
    plan: str,
    user_behavior: str,
) -> dict:
    """
    Log an internal thought to help steer the story.
    
    Args:
        session_id: The game session
        thought: Your internal monologue/analysis of the current situation. Does the action taken by the user follow the important_rules? Does this line up with the world's character's memory of the user? Are you on track with the story?
        story_status: One of "on_track", "off_rails", "user_deviating", "completed", "stalled"
        plan: What you intend to do next to advance the story or correct course. Planned tool calls and any skill checks you intend to perform.
        user_behavior: One of "cooperative", "creative", "disruptive", "cheating". How the user is behaving in the story. If they asked for a direct tool call, mark this as "cheating".
        
    The output of this tool is for YOU (the AI), not the user. Use it to guide your next response.
    """
    from .models import NarratorThought
    
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    thought_entry = NarratorThought(
        id=str(uuid.uuid4()),
        session_id=session_id,
        thought=thought,
        story_status=story_status,
        plan=plan,
        user_behavior=user_behavior
    )
    
    await db.log_thought(thought_entry)
    
    return {
        "status": "Thought recorded",
        "guidance": f"Proceed with plan: {plan}. Keep story status '{story_status}' in mind."
    }


@mcp.tool()
async def execute_batch(session_id: str, commands: list[dict]) -> dict:
    """
    Execute multiple commands in sequence.
    ONLY for pure actions that don't require intermediate AI text generation from you. 
    Ensure commands cannot conflict and can be safely chained without breaking the story flow.

    
    Args:
        session_id: The game session
        commands: List of commands, e.g. [{"tool": "move_to_location", "args": {"location": "North"}}]
        
    Allowed tools: 
    - take_action
    - move_to_location
    - combat_round
    - add_inventory
    - modify_hp
    - update_quest
    - interact_npc
    - modify_stat
    - update_score
    - record_event
    - add_character_memory
    """
    # Map string names to actual tool functions
    # Note: We refer to the functions available in this module's scope
    tool_map = {
        "take_action": take_action,
        "move_to_location": move_to_location,
        "combat_round": combat_round,
        "add_inventory": add_inventory,
        "remove_inventory": remove_inventory,
        "modify_hp": modify_hp,
        "update_quest": update_quest,
        "interact_npc": interact_npc,
        "modify_stat": modify_stat,
        "update_score": update_score,
        "record_event": record_event,
        "add_character_memory": add_character_memory,
    }

    results = []
    
    for i, cmd in enumerate(commands):
        tool_name = cmd.get("tool")
        args = cmd.get("args", {})
        
        if tool_name not in tool_map:
            results.append({"error": f"Tool '{tool_name}' not allowed in batch", "command_index": i})
            continue
            
        # Inject session_id if not present
        if "session_id" not in args:
            args["session_id"] = session_id
            
        try:
            # Call the tool function directly
            # FastMCP tools are callable wrappers
            func = tool_map[tool_name]
            result = await func(**args)
            results.append({"tool": tool_name, "result": result})
        except Exception as e:
            results.append({"tool": tool_name, "error": str(e), "command_index": i})

    return {
        "session_id": session_id,
        "batch_size": len(commands),
        "results": results
    }



@mcp.tool()
async def list_adventures() -> list[dict]:
    """List all available adventures with title and description."""
    return await db.list_adventures()


@mcp.tool()
async def list_sessions(limit: int = 20) -> list[dict]:
    """
    List recent game sessions for continuing adventures.
    """
    return await db.list_sessions(limit)


@mcp.tool()
async def generate_initial_content(adventure_id: str) -> dict:
    """
    Generate a prompt and guidance for AI to create custom initial story, words, and characters.

    This tool provides the context needed for you (the AI) to generate:
    - A custom initial story (instead of using the predefined one)
    - Custom character names and details
    - Custom location descriptions

    After calling this tool, generate your custom content and then call start_adventure()
    with the generated_story, generated_characters, and/or generated_locations parameters.

    Returns a prompt template and adventure context to guide AI generation.
    """
    await db.init_db()

    adventure = await db.get_adventure(adventure_id)
    if not adventure:
        return {
            "error": f"Adventure {adventure_id} not found",
            "suggestion": "Use list_adventures() to see available adventures"
        }

    # Extract word list info for generation guidance
    word_lists_info = []
    for wl in adventure.word_lists:
        categories = list(wl.categories.keys())
        word_lists_info.append({
            "name": wl.name,
            "description": wl.description,
            "categories": categories,
            "example_words": {cat: wl.categories[cat][:3] for cat in categories}
        })

    # Create the generation prompt
    generation_prompt = f"""You are generating a custom opening scene for the adventure "{adventure.title}".

## Adventure Context
**Description**: {adventure.description}

**Story Prompt**: {adventure.prompt}

**Character Stats Available**: {', '.join(s.name for s in adventure.stats)}
Stat Ranges: {'; '.join(f'{s.name}: {s.min_value}-{s.max_value}' for s in adventure.stats)}

**Available Word Lists for Inspiration**:
{json.dumps(word_lists_info, indent=2)}

## Task
Generate the following as JSON in this exact format:

{{
  "initial_story": "A compelling 2-3 paragraph opening that hooks the player. Include atmosphere, setting, and sense of adventure.",
  "initial_location": "The name/description of where the story begins. Can use {{word_list_name}} or {{word_list_name.category}} placeholders for dynamic variation.",
  "suggested_characters": [
    {{
      "name": "Character Name",
      "description": "Brief description of appearance, role, and personality",
      "location": "Where they are located initially",
      "properties": {{"hostile": false, "quest_giver": true}}
    }}
  ],
  "suggested_locations": [
    {{
      "name": "Location Name",
      "description": "Atmospheric description of this place",
      "connected_to": ["Adjacent location names"]
    }}
  ],
  "narrative_guidance": "A brief note for the storyteller about tone, pacing, and key themes to maintain"
}}

Generate only valid JSON, no markdown formatting or extra text."""

    return {
        "adventure_id": adventure_id,
        "adventure_title": adventure.title,
        "generation_prompt": generation_prompt,
        "next_step": "Generate custom content using the prompt above, then call start_adventure() with the generated_story, generated_characters, and generated_locations parameters",
        "example_usage": {
            "step1": "AI generates JSON using the generation_prompt",
            "step2": "AI calls start_adventure(adventure_id='{adventure_id}', generated_story='...', generated_characters=[...], generated_locations=[...])",
            "step3": "Session starts with custom-generated opening content"
        }
    }


@mcp.tool()
async def continue_adventure(session_id: str) -> dict:
    """
    Continue an existing adventure session.
    """
    session = await db.get_session(session_id)
    if not session:
        return {
            "error": f"Session {session_id} not found",
            "suggestion": "Use list_sessions() to see available sessions"
        }

    adventure = await db.get_adventure(session.adventure_id)
    if not adventure:
        return {"error": f"Adventure {session.adventure_id} not found for this session"}

    # Update last_played timestamp
    await db.update_last_played(session_id)

    # Get recent history
    recent_history = await db.get_history(session_id, limit=5)

    return {
        "session_id": session_id,
        "title": adventure.title,
        "location": session.state.location,
        "hp": f"{session.state.hp}/{session.state.max_hp}",
        "stats": session.state.stats,
        "inventory": [i.name for i in session.state.inventory],
        "quests_active": len([q for q in session.state.quests if q.status == "active"]),
        "created_at": session.created_at.isoformat(),
        "last_played": session.last_played.isoformat(),
        "recent_history": recent_history,
        "message": f"Welcome back to {adventure.title}! You are at: {session.state.location}",
    }


@mcp.tool()
async def start_adventure(
    adventure_id: str,
    randomize_initial: bool = True,
    character_name: str = None,
    roll_stats: bool = False,
    custom_stats: dict[str, int] = None,
    generated_story: str = None,
    generated_locations: list[dict] = None,
    generated_characters: list[dict] = None,
) -> dict:
    """
    Start a new game session with character customization.
    Returns session_id and initial game state.

    Args:
        adventure_id: The adventure to start
        randomize_initial: If True, use randomize_word substitution on templates (default: True)
        character_name: Optional player character name
        roll_stats: If True, roll stats using 4d6 drop lowest
        custom_stats: Optional dict of stat_name -> value for custom stat assignment
        generated_story: Optional AI-generated initial story (overrides adventure's initial_story)
        generated_locations: Optional list of AI-generated Location dicts to create in the world
        generated_characters: Optional list of AI-generated Character dicts to create in the world
    """
    # Ensure DB is initialized
    await db.init_db()

    if not await db.get_adventure(adventure_id):
        return {"error": f"Adventure {adventure_id} not found"}

    session_id = str(uuid.uuid4())
    if not await db.create_session(session_id, adventure_id):
        return {"error": "Failed to create session"}

    session = await db.get_session(session_id)
    adventure = await db.get_adventure(adventure_id)

    # Handle character naming
    if character_name:
        session.state.custom_data["character_name"] = character_name

    # Handle stat customization
    if roll_stats:
        import random
        rolled_stats = {}
        for stat_def in adventure.stats:
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            stat_value = sum(rolls[1:])
            stat_value = max(stat_def.min_value, min(stat_def.max_value, stat_value))
            rolled_stats[stat_def.name] = stat_value
        session.state.stats = rolled_stats
    elif custom_stats:
        for stat_name, value in custom_stats.items():
            if stat_name in session.state.stats:
                stat_def = next((s for s in adventure.stats if s.name == stat_name), None)
                if stat_def:
                    session.state.stats[stat_name] = max(
                        stat_def.min_value, min(stat_def.max_value, value)
                    )

    # Determine initial location and story
    if generated_story:
        # Use AI-generated story
        initial_story = generated_story
        # Extract location from adventure (or use generated if provided)
        if generated_locations and len(generated_locations) > 0:
            initial_location = generated_locations[0].get("name", adventure.initial_location)
        else:
            initial_location = adventure.initial_location
    else:
        # Use predefined adventure story with optional template processing
        if randomize_initial:
            initial_location = process_template(adventure.initial_location, adventure)
            initial_story = process_template(adventure.initial_story, adventure)
        else:
            initial_location = adventure.initial_location
            initial_story = adventure.initial_story

    session.state.location = initial_location
    await db.update_player_state(session_id, session.state)

    # Create generated locations if provided
    if generated_locations:
        for loc_data in generated_locations:
            try:
                location = Location(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    name=loc_data.get("name", f"Location {uuid.uuid4()}"),
                    description=loc_data.get("description", "A mysterious place"),
                    connected_to=loc_data.get("connected_to", []),
                    properties=loc_data.get("properties", {}),
                )
                await db.add_location(location)
            except Exception as e:
                print(f"Warning: Failed to create location: {e}")

    # Create generated characters if provided
    if generated_characters:
        for char_data in generated_characters:
            try:
                character = Character(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    name=char_data.get("name", f"NPC {uuid.uuid4()}"),
                    description=char_data.get("description", "A mysterious figure"),
                    location=char_data.get("location", initial_location),
                    stats=char_data.get("stats", {}),
                    properties=char_data.get("properties", {}),
                )
                await db.add_character(character)
            except Exception as e:
                print(f"Warning: Failed to create character: {e}")

    result = {
        "session_id": session_id,
        "title": adventure.title,
        "location": initial_location,
        "story": initial_story,
        "hp": session.state.hp,
        "stats": session.state.stats,
    }

    if character_name:
        result["character_name"] = character_name

    if generated_characters:
        result["generated_characters"] = len(generated_characters)

    if generated_locations:
        result["generated_locations"] = len(generated_locations)

    return result


@mcp.tool()
async def get_state(session_id: str) -> dict:
    """Get current game state including location, stats, score, inventory, hp, quests."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    return {
        "session_id": session_id,
        "location": session.state.location,
        "hp": session.state.hp,
        "max_hp": session.state.max_hp,
        "stats": session.state.stats,
        "inventory": [i.model_dump() for i in session.state.inventory],
        "quests": [q.model_dump() for q in session.state.quests],
        "relationships": session.state.relationships,
        "score": session.state.score,
        "custom_data": session.state.custom_data,
    }


@mcp.tool()
async def take_action(session_id: str, action: str, stat_name: str = None, difficulty_class: int = 10) -> dict:
    """
    Perform a fictional in-game action for the player character.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    # Perform dice check if stat is used
    if stat_name:
        if stat_name not in session.state.stats:
            return {"error": f"Stat '{stat_name}' not found in this adventure"}

        stat_value = session.state.stats[stat_name]
        roll_result = stat_check(stat_value, difficulty_class)
        success = roll_result.success
    else:
        roll_result = None
        success = True

    # Record action
    from .models import Action as ActionModel
    from datetime import datetime
    
    action_record = ActionModel(
        session_id=session_id,
        action_text=action,
        stat_used=stat_name,
        difficulty_class=difficulty_class,
        timestamp=datetime.now()
    )
    await db.add_action(
        session_id, 
        action_record, 
        "Success" if success else "Failure", 
        0,
        dice_roll=roll_result.model_dump() if roll_result else None
    )

    return {
        "session_id": session_id,
        "action": action,
        "success": success,
        "dice_roll": roll_result.model_dump() if roll_result else None,
        "score_change": 10 if success else 0,
        "prompt": f"Generate a story outcome for this {'successful' if success else 'failed'} action: {action}",
    }


@mcp.tool()
async def combat_round(
    session_id: str,
    target_name: str,
    player_action: str,
    attack_stat: str = "Strength",
    target_ac: int = 12,
    damage_dice: str = "1d6"
) -> dict:
    """
    Resolve a round of combat.
    1. Player attacks Target (d20 + stat vs AC).
    2. If hit, calculate damage.
    3. Target attacks Player (automatic damage for simplicity or AI determined).
    4. Updates Player HP.

    Args:
        session_id: Game session
        target_name: Name of enemy
        player_action: Description of attack (e.g., "Swing sword")
        attack_stat: Stat to use for attack roll
        target_ac: Enemy Armor Class (Difficulty to hit)
        damage_dice: Damage on hit (e.g. "1d6", "1d8+2")
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    if attack_stat not in session.state.stats:
        return {"error": f"Stat '{attack_stat}' not found"}

    # Player Attack
    stat_value = session.state.stats[attack_stat]
    attack_roll = stat_check(stat_value, target_ac)
    
    damage = 0
    message = ""
    
    if attack_roll.success:
        # Simple damage calculation for prototype
        import random
        if "d" in damage_dice:
            num, sides = map(int, damage_dice.split("+")[0].split("d"))
            base_dmg = sum(random.randint(1, sides) for _ in range(num))
            # Add flat bonus if present
            bonus = int(damage_dice.split("+")[1]) if "+" in damage_dice else 0
            damage = base_dmg + bonus
        else:
            damage = int(damage_dice)
        
        message = f"HIT! Dealt {damage} damage to {target_name}."
    else:
        message = f"MISS! Your attack against {target_name} failed."

    # Enemy Counter-Attack (Simplified: AI determines outcome, we just prompt for it)
    # In a full game, we'd track enemy stats in DB. For now, this tool handles the mechanics of the player's turn.
    
    return {
        "success": attack_roll.success,
        "attack_roll": attack_roll.model_dump(),
        "damage_dealt": damage,
        "message": message,
        "current_hp": session.state.hp,
        "prompt": f"Describe the combat round. Player {message}. Then describe {target_name}'s counter-attack and specify damage to player using modify_hp tool if needed."
    }


@mcp.tool()
async def modify_hp(session_id: str, amount: int, reason: str = None) -> dict:
    """
    Modify player HP (healing or damage).
    Positive amount heals, negative amount deals damage.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    old_hp = session.state.hp
    new_hp = session.state.hp + amount
    new_hp = max(0, min(session.state.max_hp, new_hp))
    
    session.state.hp = new_hp
    await db.update_player_state(session_id, session.state)
    
    return {
        "old_hp": old_hp,
        "new_hp": new_hp,
        "change": amount,
        "reason": reason,
        "status": "Unconscious/Dead" if new_hp == 0 else "Alive"
    }


@mcp.tool()
async def update_quest(
    session_id: str,
    quest_id: str,
    title: str = None,
    status: str = None, # active, completed, failed
    new_objective: str = None,
    complete_objective: str = None
) -> dict:
    """
    Manage quests. Can create new quest (provide title) or update existing.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    quest = next((q for q in session.state.quests if q.id == quest_id), None)
    
    # Create new if not exists and title provided
    if not quest and title:
        quest = QuestStatus(
            id=quest_id,
            title=title,
            description="New Quest",
            status="active",
            objectives=[new_objective] if new_objective else []
        )
        session.state.quests.append(quest)
        await db.update_player_state(session_id, session.state)
        return {"message": f"Quest '{title}' started.", "quest": quest.model_dump()}
    
    if not quest:
        return {"error": f"Quest {quest_id} not found"}

    updates = []
    if status:
        quest.status = status
        updates.append(f"Status: {status}")
    
    if new_objective:
        quest.objectives.append(new_objective)
        updates.append("Added objective")
        
    if complete_objective and complete_objective in quest.objectives:
        if complete_objective not in quest.completed_objectives:
            quest.completed_objectives.append(complete_objective)
            updates.append("Completed objective")

    await db.update_player_state(session_id, session.state)
    return {"message": "Quest updated", "updates": updates, "quest": quest.model_dump()}


@mcp.tool()
async def interact_npc(session_id: str, npc_name: str, sentiment_change: int) -> dict:
    """
    Update relationship/reputation with an NPC.
    sentiment_change: +ve for good interaction, -ve for bad.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
        
    current = session.state.relationships.get(npc_name, 0)
    new_val = max(-100, min(100, current + sentiment_change))
    session.state.relationships[npc_name] = new_val
    
    await db.update_player_state(session_id, session.state)
    
    status = "Neutral"
    if new_val > 50: status = "Friendly"
    if new_val > 80: status = "Ally"
    if new_val < -50: status = "Hostile"
    if new_val < -80: status = "Nemesis"
    
    return {
        "npc": npc_name,
        "old_value": current,
        "new_value": new_val,
        "status": status
    }


@mcp.tool()
async def modify_stat(session_id: str, stat_name: str, change: int) -> dict:
    """
    Increase or decrease a player stat by the specified amount.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if stat_name not in session.state.stats:
        return {"error": f"Stat '{stat_name}' not found"}

    adventure = await db.get_adventure(session.adventure_id)
    stat_def = next((s for s in adventure.stats if s.name == stat_name), None)

    old_value = session.state.stats[stat_name]
    new_value = old_value + change

    # Clamp to stat bounds
    if stat_def:
        new_value = max(stat_def.min_value, min(stat_def.max_value, new_value))
    else:
        new_value = max(0, min(20, new_value))

    session.state.stats[stat_name] = new_value
    await db.update_player_state(session_id, session.state)

    return {
        "stat": stat_name,
        "old_value": old_value,
        "new_value": new_value,
        "change": change,
    }


@mcp.tool()
async def roll_check(session_id: str, stat_name: str = None, difficulty_class: int = 10) -> dict:
    """Perform a stat check or plain d20 roll."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if stat_name:
        if stat_name not in session.state.stats:
            return {"error": f"Stat '{stat_name}' not found"}
        stat_value = session.state.stats[stat_name]
        result = stat_check(stat_value, difficulty_class)
    else:
        result = dice_roll_check(difficulty_class=difficulty_class)

    return result.model_dump()


@mcp.tool()
async def move_to_location(session_id: str, location: str) -> dict:
    """Move player to a new location."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    session.state.location = location
    await db.update_player_state(session_id, session.state)

    return {"location": location, "message": f"Moved to {location}"}


@mcp.tool()
async def add_inventory(session_id: str, item_name: str, quantity: int = 1, properties: dict = None) -> dict:
    """
    Add item to inventory with rich support.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    # Check if item already exists
    existing = next((i for i in session.state.inventory if i.name == item_name), None)
    
    if existing:
        existing.quantity += quantity
    else:
        new_item = InventoryItem(
            id=str(uuid.uuid4()),
            name=item_name,
            description="Added to inventory",
            quantity=quantity,
            properties=properties or {}
        )
        session.state.inventory.append(new_item)

    await db.update_player_state(session_id, session.state)

    return {
        "message": f"Added {quantity}x {item_name}",
        "current_inventory": [f"{i.quantity}x {i.name}" for i in session.state.inventory]
    }


@mcp.tool()
async def remove_inventory(session_id: str, item_name: str, quantity: int = 1) -> dict:
    """
    Remove item from inventory.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    item = next((i for i in session.state.inventory if i.name == item_name), None)
    if not item:
        return {"error": f"Item {item_name} not found in inventory"}
        
    if item.quantity > quantity:
        item.quantity -= quantity
        removed = quantity
    else:
        removed = item.quantity
        session.state.inventory.remove(item)

    await db.update_player_state(session_id, session.state)

    return {
        "message": f"Removed {removed}x {item_name}",
        "remaining": item.quantity if item in session.state.inventory else 0
    }


@mcp.tool()
async def update_score(session_id: str, points: int) -> dict:
    """Add or subtract points from score."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    session.state.score += points
    await db.update_player_state(session_id, session.state)

    return {"score": session.state.score, "change": points}


@mcp.tool()
async def get_history(session_id: str, limit: int = 20) -> dict:
    """Get action history for this session."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    history = await db.get_history(session_id, limit)
    return {"session_id": session_id, "history": history}


@mcp.tool()
async def randomize_word(
    session_id: str,
    word_list_name: str,
    category_name: str = None,
    use_predefined: bool = True,
) -> dict:
    """
    Get a random word from adventure's predefined list or generate a prompt for AI.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)

    if use_predefined:
        word = get_random_word(adventure, word_list_name, category_name)
        if word:
            return {
                "source": "predefined",
                "word": word,
                "word_list": word_list_name,
                "category": category_name or "all",
            }
        else:
            return {
                "error": f"Word list '{word_list_name}' not found",
                "available_lists": [wl.name for wl in adventure.word_lists],
            }
    else:
        prompt = generate_word_prompt(
            word_list_name,
            category_name,
            context=adventure.title,
        )
        return {
            "source": "ai_generated",
            "prompt": prompt,
            "word_list": word_list_name,
            "category": category_name or "any",
        }


@mcp.tool()
async def summarize_progress(
    session_id: str,
    summary: str,
    key_events: list[str] = None,
    character_changes: list[str] = None,
) -> dict:
    """
    Create a summary of the current game session.
    """
    from .models import SessionSummary

    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    summary_id = str(uuid.uuid4())
    session_summary = SessionSummary(
        id=summary_id,
        session_id=session_id,
        summary=summary,
        key_events=key_events or [],
        character_changes=character_changes or [],
    )

    await db.add_session_summary(session_summary)

    return {
        "summary_id": summary_id,
        "session_id": session_id,
        "message": "Session summary created successfully",
    }


@mcp.tool()
async def get_adventure_summary(session_id: str) -> dict:
    """
    Get all session summaries.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)
    summaries = await db.get_session_summaries(session_id)

    return {
        "session_id": session_id,
        "adventure": adventure.title,
        "total_summaries": len(summaries),
        "summaries": [
            {
                "summary": s.summary,
                "key_events": s.key_events,
                "character_changes": s.character_changes,
                "created_at": s.created_at.isoformat(),
            }
            for s in summaries
        ],
        "current_state": {
            "location": session.state.location,
            "score": session.state.score,
            "hp": f"{session.state.hp}/{session.state.max_hp}",
            "character_name": session.state.custom_data.get("character_name", "Unknown Adventurer"),
        },
    }


@mcp.resource("adventure://prompt/{adventure_id}")
async def adventure_prompt(adventure_id: str) -> Resource:
    """Get adventure prompt template for AI to generate story beats."""
    adventure = await db.get_adventure(adventure_id)
    if not adventure:
        return Resource(uri=f"adventure://prompt/{adventure_id}", contents="Not found")

    prompt_content = f"""# {adventure.title}

## Description
{adventure.description}

## Story Prompt
{adventure.prompt}

## Available Stats
{json.dumps([{"name": s.name, "description": s.description, "range": f"{s.min_value}-{s.max_value}"} for s in adventure.stats], indent=2)}

## Initial Location
{adventure.initial_location}

## Instructions
Use this prompt to generate engaging story beats. Track HP, Quests, and Stats. Combat is available via combat_round."""

    return Resource(
        uri=f"adventure://prompt/{adventure_id}",
        contents=prompt_content,
        mime_type="text/plain",
    )


@mcp.resource("session://state/{session_id}")
async def session_state(session_id: str) -> Resource:
    """Get session state in AI-readable JSON format."""
    session = await db.get_session(session_id)
    if not session:
        return Resource(uri=f"session://state/{session_id}", contents="Not found")

    adventure = await db.get_adventure(session.adventure_id)
    state_content = json.dumps({
        "session_id": session_id,
        "adventure": adventure.title,
        "location": session.state.location,
        "score": session.state.score,
        "hp": session.state.hp,
        "max_hp": session.state.max_hp,
        "stats": session.state.stats,
        "inventory": [i.model_dump() for i in session.state.inventory],
        "quests": [q.model_dump() for q in session.state.quests],
        "custom_data": session.state.custom_data,
    }, indent=2)

    return Resource(
        uri=f"session://state/{session_id}",
        contents=state_content,
        mime_type="application/json",
    )


async def _add_memory_to_character(character: Character, description: str, type: str, importance: int, related_entities: list[str] = None, tags: list[str] = None):
    """Helper to add a memory to a character and save it."""
    memory = Memory(
        id=str(uuid.uuid4()),
        description=description,
        timestamp=datetime.now(),
        type=type,
        importance=importance,
        related_entities=related_entities or [],
        tags=tags or []
    )
    character.memories.append(memory)
    
    # Simple decay: Keep max 50, remove oldest of lowest importance
    if len(character.memories) > 50:
        # Sort by importance (asc), then timestamp (asc)
        character.memories.sort(key=lambda x: (x.importance, x.timestamp))
        # Remove the first one (least important, oldest)
        character.memories.pop(0)
        
    await db.update_character(character)


@mcp.tool()
async def record_event(session_id: str, event_description: str, location: str = None, importance: int = 1, tags: list[str] = None) -> dict:
    """
    Record an event that occurred in the world. Call this after any significant event (e.g., "Player killed the goblin king", "An explosion rocked the town square"). It will automatically update
     the state of all witnesses in the location.
    Automatically triggers the "Perception Module" to distribute memories to characters (witnesses) in the location.
    Use this when something significant happens that NPCs should know about.
    Tags can be used to categorize the event (e.g., ["hostile", "magic", "theft"]).
    Keep it short and concise. Use the least amount of words possible to describe the event but don't leave out important details.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    loc = location or session.state.location
    characters = await db.list_characters(session_id)
    # Perception Module: Find witnesses
    witnesses = [c for c in characters if c.location == loc]
    
    results = []
    for char in witnesses:
        await _add_memory_to_character(char, event_description, "observation", importance, tags=tags)
        results.append(char.name)
        
    return {
        "message": f"Event recorded at {loc}.",
        "witness_count": len(results),
        "witnesses": results
    }


@mcp.tool()
async def add_character_memory(session_id: str, character_name: str, description: str, type: str = "rumor", importance: int = 1, tags: list[str] = None) -> dict:
    """
    Manually implant a memory into a specific character (e.g., you tell them something, or they read a note).
    Use this for specific, non-public events, like whispering a secret to an NPC or spreading a rumor.
    Type can be "observation", "interaction", "rumor".
    Keep it short and concise. Use the least amount of words possible to describe the event but don't leave out important details.

    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
        
    characters = await db.list_characters(session_id)
    character = next((c for c in characters if c.name.lower() == character_name.lower()), None)
    
    if not character:
        return {"error": f"Character {character_name} not found"}
        
    await _add_memory_to_character(character, description, type, importance, tags=tags)
    
    return {
        "message": f"Memory added to {character.name}",
        "memory": description
    }


@mcp.tool()
async def get_character_memories(session_id: str, character_name: str, limit: int = 10) -> dict:
    """
    Retrieve memories for a specific character to inform their behavior and disposition.
    Memories are returned sorted by importance and recency.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    characters = await db.list_characters(session_id)
    character = next((c for c in characters if c.name.lower() == character_name.lower()), None)
    
    if not character:
        return {"error": f"Character {character_name} not found"}
        
    # Memory Retrieval: Sort by importance (desc) then timestamp (desc)
    sorted_memories = sorted(character.memories, key=lambda m: (m.importance, m.timestamp.timestamp()), reverse=True)
    
    return {
        "character": character.name,
        "memories": [m.model_dump() for m in sorted_memories[:limit]]
    }


async def load_sample_adventures():
    """Load adventures from JSON files in the adventures directory."""
    await db.init_db()
    adventures_dir = Path(__file__).parent / "adventures"

    if not adventures_dir.exists():
        print(f"Warning: Adventures directory not found at {adventures_dir}")
        return

    for file_path in adventures_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                adv_data = json.load(f)

            required_fields = ["id", "title", "description", "prompt", "stats", "word_lists", "initial_location", "initial_story"]
            if not all(key in adv_data for key in required_fields):
                print(f"Skipping {file_path.name}: Missing required fields. Has: {list(adv_data.keys())}")
                continue

            stats = [StatDefinition(**s) for s in adv_data.pop("stats")]
            word_lists = [WordList(**wl) for wl in adv_data.pop("word_lists")]
            # Ensure starting_hp is present, default to 10 if missing
            if "starting_hp" not in adv_data:
                adv_data["starting_hp"] = 10
            adventure = Adventure(stats=stats, word_lists=word_lists, **adv_data)
            await db.add_adventure(adventure)
            print(f"Loaded adventure: {adventure.title} ({adventure.id}) - HP: {adventure.starting_hp}")
        except Exception as e:
            print(f"Error loading adventure from {file_path.name}: {e}")
