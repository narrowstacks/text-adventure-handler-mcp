"""FastMCP server for text adventure handler."""
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import Resource

from .database import AdventureDB
from .models import Adventure, StatDefinition, WordList, Character, Location, Item, InventoryItem, QuestStatus, Memory, StatusEffect, Faction
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
    - take_action, move_to_location, combat_round
    - manage_inventory, modify_hp, modify_stat, update_score
    - update_quest, interact_npc, record_event, add_character_memory
    - manage_character, manage_location, manage_item
    - manage_status_effect, manage_time, manage_faction, manage_economy, manage_summary
    """
    # Map string names to actual tool functions
    # Note: We refer to the functions available in this module's scope
    tool_map = {
        "take_action": take_action,
        "move_to_location": move_to_location,
        "combat_round": combat_round,
        "manage_inventory": manage_inventory,
        "modify_hp": modify_hp,
        "update_quest": update_quest,
        "interact_npc": interact_npc,
        "modify_stat": modify_stat,
        "update_score": update_score,
        "record_event": record_event,
        "add_character_memory": add_character_memory,
        "manage_character": manage_character,
        "manage_location": manage_location,
        "manage_item": manage_item,
        "manage_status_effect": manage_status_effect,
        "manage_time": manage_time,
        "manage_faction": manage_faction,
        "manage_economy": manage_economy,
        "manage_summary": manage_summary,
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
async def get_session_info(
    session_id: str,
    include_state: bool = True,
    include_history: bool = False,
    include_character_memories: str = None,
    history_limit: int = 20,
    memory_limit: int = 10,
    include_nearby_characters: bool = False,
    include_available_items: bool = False
) -> dict:
    """
    Get comprehensive session information with optional components.

    This consolidated tool replaces get_state(), get_history(), and get_character_memories().

    Args:
        session_id: The game session ID
        include_state: Include current game state (location, stats, inventory, hp, quests, etc.)
        include_history: Include action history
        include_character_memories: Character name to retrieve memories for (None to skip)
        history_limit: Maximum number of history entries to return (default: 20)
        memory_limit: Maximum number of memories to return (default: 10)
        include_nearby_characters: Include characters at current location
        include_available_items: Include items at current location

    Returns a dict with requested information components.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    result = {"session_id": session_id}

    # State information
    if include_state:
        result["state"] = {
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

    # History information
    if include_history:
        history = await db.get_history(session_id, history_limit)
        result["history"] = history

    # Character memories
    if include_character_memories:
        characters = await db.list_characters(session_id)
        character = next((c for c in characters if c.name.lower() == include_character_memories.lower()), None)

        if character:
            sorted_memories = sorted(character.memories, key=lambda m: (m.importance, m.timestamp.timestamp()), reverse=True)
            result["character_memories"] = {
                "character": character.name,
                "memories": [m.model_dump() for m in sorted_memories[:memory_limit]]
            }
        else:
            result["character_memories"] = {"error": f"Character {include_character_memories} not found"}

    # Nearby characters
    if include_nearby_characters:
        characters = await db.list_characters(session_id)
        nearby = [
            {"id": c.id, "name": c.name, "description": c.description}
            for c in characters
            if c.location == session.state.location
        ]
        result["nearby_characters"] = nearby

    # Available items at location
    if include_available_items:
        items = await db.list_items(session_id)
        available = [
            {"id": i.id, "name": i.name, "description": i.description}
            for i in items
            if i.location == session.state.location
        ]
        result["available_items"] = available

    return result


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
        "player_action": player_action,
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
async def manage_inventory(
    session_id: str,
    action: str,
    item_name: str = None,
    quantity: int = 1,
    properties: dict = None
) -> dict:
    """
    Modular tool for inventory management operations.

    This consolidated tool replaces add_inventory() and remove_inventory().

    Actions:
    - add: Add item to inventory (requires item_name, optional quantity and properties)
    - remove: Remove item from inventory (requires item_name, optional quantity)
    - update: Update item properties (requires item_name and properties)
    - check: Check if specific item exists in inventory (requires item_name)
    - list: List all inventory items (no additional parameters needed)
    - use: Mark item as used/consumed (requires item_name, optional quantity)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "add":
        if not item_name:
            return {"error": "item_name required for add action"}

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
            "success": True,
            "action": "add",
            "message": f"Added {quantity}x {item_name}",
            "current_inventory": [f"{i.quantity}x {i.name}" for i in session.state.inventory]
        }

    elif action == "remove":
        if not item_name:
            return {"error": "item_name required for remove action"}

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
            "success": True,
            "action": "remove",
            "message": f"Removed {removed}x {item_name}",
            "remaining": item.quantity if item in session.state.inventory else 0
        }

    elif action == "update":
        if not item_name:
            return {"error": "item_name required for update action"}
        if not properties:
            return {"error": "properties required for update action"}

        item = next((i for i in session.state.inventory if i.name == item_name), None)
        if not item:
            return {"error": f"Item {item_name} not found in inventory"}

        item.properties.update(properties)
        await db.update_player_state(session_id, session.state)

        return {
            "success": True,
            "action": "update",
            "message": f"Updated properties for {item_name}",
            "properties": item.properties
        }

    elif action == "check":
        if not item_name:
            return {"error": "item_name required for check action"}

        item = next((i for i in session.state.inventory if i.name == item_name), None)
        if not item:
            return {
                "success": True,
                "action": "check",
                "exists": False,
                "item_name": item_name
            }

        return {
            "success": True,
            "action": "check",
            "exists": True,
            "item": item.model_dump()
        }

    elif action == "list":
        return {
            "success": True,
            "action": "list",
            "inventory": [i.model_dump() for i in session.state.inventory],
            "summary": [f"{i.quantity}x {i.name}" for i in session.state.inventory]
        }

    elif action == "use":
        if not item_name:
            return {"error": "item_name required for use action"}

        item = next((i for i in session.state.inventory if i.name == item_name), None)
        if not item:
            return {"error": f"Item {item_name} not found in inventory"}

        # Check if item is consumable
        if item.properties.get("consumable", False):
            if item.quantity > quantity:
                item.quantity -= quantity
                removed = quantity
            else:
                removed = item.quantity
                session.state.inventory.remove(item)

            await db.update_player_state(session_id, session.state)

            return {
                "success": True,
                "action": "use",
                "message": f"Used {removed}x {item_name}",
                "consumed": True,
                "remaining": item.quantity if item in session.state.inventory else 0
            }
        else:
            # Mark as used but don't remove
            item.properties["last_used"] = datetime.now().isoformat()
            item.properties["use_count"] = item.properties.get("use_count", 0) + 1
            await db.update_player_state(session_id, session.state)

            return {
                "success": True,
                "action": "use",
                "message": f"Used {item_name}",
                "consumed": False,
                "use_count": item.properties["use_count"]
            }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: add, remove, update, check, list, use"}


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
async def manage_summary(
    session_id: str,
    action: str,
    summary: str = None,
    key_events: list[str] = None,
    character_changes: list[str] = None,
    summary_id: str = None
) -> dict:
    """
    Modular tool for session summary management.

    This consolidated tool replaces summarize_progress() and get_adventure_summary().

    Actions:
    - create: Create new session summary (requires summary, optional key_events and character_changes)
    - get: Get all session summaries with adventure context
    - get_latest: Get only the most recent summary
    - delete: Delete a specific summary (requires summary_id)
    """
    from .models import SessionSummary

    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not summary:
            return {"error": "summary required for create action"}

        new_summary_id = str(uuid.uuid4())
        session_summary = SessionSummary(
            id=new_summary_id,
            session_id=session_id,
            summary=summary,
            key_events=key_events or [],
            character_changes=character_changes or [],
        )

        await db.add_session_summary(session_summary)

        return {
            "success": True,
            "action": "create",
            "summary_id": new_summary_id,
            "session_id": session_id,
            "message": "Session summary created successfully",
        }

    elif action == "get":
        adventure = await db.get_adventure(session.adventure_id)
        summaries = await db.get_session_summaries(session_id)

        return {
            "success": True,
            "action": "get",
            "session_id": session_id,
            "adventure": adventure.title,
            "total_summaries": len(summaries),
            "summaries": [
                {
                    "id": s.id,
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

    elif action == "get_latest":
        summaries = await db.get_session_summaries(session_id)

        if not summaries:
            return {
                "success": True,
                "action": "get_latest",
                "message": "No summaries found for this session"
            }

        latest = summaries[-1]  # Assuming summaries are ordered by creation time

        return {
            "success": True,
            "action": "get_latest",
            "session_id": session_id,
            "summary": {
                "id": latest.id,
                "summary": latest.summary,
                "key_events": latest.key_events,
                "character_changes": latest.character_changes,
                "created_at": latest.created_at.isoformat(),
            }
        }

    elif action == "delete":
        if not summary_id:
            return {"error": "summary_id required for delete action"}

        # Note: This assumes a delete_session_summary method exists in the database
        # If it doesn't exist, we would need to add it
        try:
            await db.delete_session_summary(summary_id)
            return {
                "success": True,
                "action": "delete",
                "summary_id": summary_id,
                "message": "Summary deleted successfully"
            }
        except AttributeError:
            return {"error": "Delete functionality not yet implemented in database layer"}

    else:
        return {"error": f"Unknown action: {action}. Valid actions: create, get, get_latest, delete"}


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
        "currency": session.state.currency,
        "game_time": session.state.game_time,
        "game_day": session.state.game_day,
    }, indent=2)

    return Resource(
        uri=f"session://state/{session_id}",
        contents=state_content,
        mime_type="application/json",
    )


@mcp.resource("session://history/{session_id}")
async def session_history(session_id: str) -> Resource:
    """Get action history for a session."""
    history = await db.get_history(session_id, limit=100)
    if not history:
        return Resource(uri=f"session://history/{session_id}", contents="[]")

    history_content = json.dumps(history, indent=2)
    return Resource(
        uri=f"session://history/{session_id}",
        contents=history_content,
        mime_type="application/json",
    )


@mcp.resource("session://characters/{session_id}")
async def session_characters(session_id: str) -> Resource:
    """Get all characters in a session."""
    characters = await db.list_characters(session_id)
    if not characters:
        return Resource(uri=f"session://characters/{session_id}", contents="[]")

    characters_content = json.dumps([c.model_dump() for c in characters], indent=2, default=str)
    return Resource(
        uri=f"session://characters/{session_id}",
        contents=characters_content,
        mime_type="application/json",
    )


@mcp.resource("session://locations/{session_id}")
async def session_locations(session_id: str) -> Resource:
    """Get all locations in a session."""
    locations = await db.list_locations(session_id)
    if not locations:
        return Resource(uri=f"session://locations/{session_id}", contents="[]")

    locations_content = json.dumps([l.model_dump() for l in locations], indent=2, default=str)
    return Resource(
        uri=f"session://locations/{session_id}",
        contents=locations_content,
        mime_type="application/json",
    )


@mcp.resource("session://items/{session_id}")
async def session_items(session_id: str) -> Resource:
    """Get all items in a session."""
    items = await db.list_items(session_id)
    if not items:
        return Resource(uri=f"session://items/{session_id}", contents="[]")

    items_content = json.dumps([i.model_dump() for i in items], indent=2, default=str)
    return Resource(
        uri=f"session://items/{session_id}",
        contents=items_content,
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
async def manage_character(
    session_id: str,
    action: str,
    character_id: str | None = None,
    character_data: dict | None = None
) -> dict:
    """
    Modular tool for character CRUD operations.

    Actions:
    - create: Create new character (requires character_data with: name, description, location, stats?, properties?)
    - read: Get character by ID (requires character_id)
    - update: Update character (requires character_id and character_data)
    - delete: Delete character (requires character_id)
    - list: List all characters in session
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not character_data:
            return {"error": "character_data required for create action"}
        char_id = character_data.get("id", f"char_{uuid.uuid4().hex[:8]}")
        character = Character(
            id=char_id,
            session_id=session_id,
            name=character_data["name"],
            description=character_data["description"],
            location=character_data["location"],
            stats=character_data.get("stats", {}),
            properties=character_data.get("properties", {}),
            memories=[]
        )
        await db.add_character(character)
        return {"success": True, "action": "create", "character_id": char_id}

    elif action == "read":
        if not character_id:
            return {"error": "character_id required for read action"}
        character = await db.get_character(character_id)
        if not character:
            return {"error": f"Character {character_id} not found"}
        return {"success": True, "action": "read", "data": character.model_dump()}

    elif action == "update":
        if not character_id:
            return {"error": "character_id required for update action"}
        if not character_data:
            return {"error": "character_data required for update action"}
        character = await db.get_character(character_id)
        if not character:
            return {"error": f"Character {character_id} not found"}
        # Update fields
        if "name" in character_data:
            character.name = character_data["name"]
        if "description" in character_data:
            character.description = character_data["description"]
        if "location" in character_data:
            character.location = character_data["location"]
        if "stats" in character_data:
            character.stats = character_data["stats"]
        if "properties" in character_data:
            character.properties = character_data["properties"]
        await db.update_character(character)
        return {"success": True, "action": "update", "character_id": character_id}

    elif action == "delete":
        if not character_id:
            return {"error": "character_id required for delete action"}
        await db.delete_character(character_id)
        return {"success": True, "action": "delete", "character_id": character_id}

    elif action == "list":
        characters = await db.list_characters(session_id)
        return {
            "success": True,
            "action": "list",
            "characters": [{"id": c.id, "name": c.name, "location": c.location} for c in characters]
        }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: create, read, update, delete, list"}


@mcp.tool()
async def manage_location(
    session_id: str,
    action: str,
    location_id: str | None = None,
    location_data: dict | None = None
) -> dict:
    """
    Modular tool for location CRUD operations.

    Actions:
    - create: Create new location (requires location_data with: name, description, connected_to?, properties?)
    - read: Get location by ID (requires location_id)
    - update: Update location (requires location_id and location_data)
    - delete: Delete location (requires location_id)
    - list: List all locations in session
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not location_data:
            return {"error": "location_data required for create action"}
        loc_id = location_data.get("id", f"loc_{uuid.uuid4().hex[:8]}")
        location = Location(
            id=loc_id,
            session_id=session_id,
            name=location_data["name"],
            description=location_data["description"],
            connected_to=location_data.get("connected_to", []),
            properties=location_data.get("properties", {})
        )
        await db.add_location(location)
        return {"success": True, "action": "create", "location_id": loc_id}

    elif action == "read":
        if not location_id:
            return {"error": "location_id required for read action"}
        location = await db.get_location(location_id)
        if not location:
            return {"error": f"Location {location_id} not found"}
        return {"success": True, "action": "read", "data": location.model_dump()}

    elif action == "update":
        if not location_id:
            return {"error": "location_id required for update action"}
        if not location_data:
            return {"error": "location_data required for update action"}
        location = await db.get_location(location_id)
        if not location:
            return {"error": f"Location {location_id} not found"}
        if "name" in location_data:
            location.name = location_data["name"]
        if "description" in location_data:
            location.description = location_data["description"]
        if "connected_to" in location_data:
            location.connected_to = location_data["connected_to"]
        if "properties" in location_data:
            location.properties = location_data["properties"]
        await db.update_location(location)
        return {"success": True, "action": "update", "location_id": location_id}

    elif action == "delete":
        if not location_id:
            return {"error": "location_id required for delete action"}
        await db.delete_location(location_id)
        return {"success": True, "action": "delete", "location_id": location_id}

    elif action == "list":
        locations = await db.list_locations(session_id)
        return {
            "success": True,
            "action": "list",
            "locations": [{"id": l.id, "name": l.name} for l in locations]
        }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: create, read, update, delete, list"}


@mcp.tool()
async def manage_item(
    session_id: str,
    action: str,
    item_id: str | None = None,
    item_data: dict | None = None
) -> dict:
    """
    Modular tool for item CRUD operations.

    Actions:
    - create: Create new item (requires item_data with: name, description, location?, properties?)
    - read: Get item by ID (requires item_id)
    - update: Update item (requires item_id and item_data)
    - delete: Delete item (requires item_id)
    - list: List all items in session
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not item_data:
            return {"error": "item_data required for create action"}
        itm_id = item_data.get("id", f"item_{uuid.uuid4().hex[:8]}")
        item = Item(
            id=itm_id,
            session_id=session_id,
            name=item_data["name"],
            description=item_data["description"],
            location=item_data.get("location"),
            properties=item_data.get("properties", {})
        )
        await db.add_item(item)
        return {"success": True, "action": "create", "item_id": itm_id}

    elif action == "read":
        if not item_id:
            return {"error": "item_id required for read action"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        return {"success": True, "action": "read", "data": item.model_dump()}

    elif action == "update":
        if not item_id:
            return {"error": "item_id required for update action"}
        if not item_data:
            return {"error": "item_data required for update action"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        if "name" in item_data:
            item.name = item_data["name"]
        if "description" in item_data:
            item.description = item_data["description"]
        if "location" in item_data:
            item.location = item_data["location"]
        if "properties" in item_data:
            item.properties = item_data["properties"]
        await db.update_item(item)
        return {"success": True, "action": "update", "item_id": item_id}

    elif action == "delete":
        if not item_id:
            return {"error": "item_id required for delete action"}
        await db.delete_item(item_id)
        return {"success": True, "action": "delete", "item_id": item_id}

    elif action == "list":
        items = await db.list_items(session_id)
        return {
            "success": True,
            "action": "list",
            "items": [{"id": i.id, "name": i.name, "location": i.location} for i in items]
        }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: create, read, update, delete, list"}


@mcp.tool()
async def manage_status_effect(
    session_id: str,
    action: str,
    effect_id: str | None = None,
    effect_data: dict | None = None
) -> dict:
    """
    Modular tool for status effect management.

    Actions:
    - apply: Apply new status effect (requires effect_data with: name, description, duration, stat_modifiers?, properties?)
    - remove: Remove status effect (requires effect_id)
    - list: List all active status effects
    - update: Update effect duration or modifiers (requires effect_id and effect_data)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "apply":
        if not effect_data:
            return {"error": "effect_data required for apply action"}
        eff_id = effect_data.get("id", f"effect_{uuid.uuid4().hex[:8]}")
        effect = StatusEffect(
            id=eff_id,
            session_id=session_id,
            name=effect_data["name"],
            description=effect_data["description"],
            duration=effect_data["duration"],
            stat_modifiers=effect_data.get("stat_modifiers", {}),
            properties=effect_data.get("properties", {})
        )
        await db.add_status_effect(effect)
        return {"success": True, "action": "apply", "effect_id": eff_id}

    elif action == "remove":
        if not effect_id:
            return {"error": "effect_id required for remove action"}
        await db.delete_status_effect(effect_id)
        return {"success": True, "action": "remove", "effect_id": effect_id}

    elif action == "list":
        effects = await db.list_status_effects(session_id, active_only=True)
        return {
            "success": True,
            "action": "list",
            "effects": [{"id": e.id, "name": e.name, "duration": e.duration, "modifiers": e.stat_modifiers} for e in effects]
        }

    elif action == "update":
        if not effect_id:
            return {"error": "effect_id required for update action"}
        if not effect_data:
            return {"error": "effect_data required for update action"}
        effect = await db.get_status_effect(effect_id)
        if not effect:
            return {"error": f"Effect {effect_id} not found"}
        if "duration" in effect_data:
            effect.duration = effect_data["duration"]
        if "stat_modifiers" in effect_data:
            effect.stat_modifiers = effect_data["stat_modifiers"]
        if "properties" in effect_data:
            effect.properties = effect_data["properties"]
        await db.update_status_effect(effect)
        return {"success": True, "action": "update", "effect_id": effect_id}

    else:
        return {"error": f"Unknown action: {action}. Valid actions: apply, remove, list, update"}


@mcp.tool()
async def manage_time(
    session_id: str,
    action: str,
    hours: int | None = None,
    reason: str | None = None
) -> dict:
    """
    Modular tool for time management (AI-controlled).

    Actions:
    - advance: Advance time by hours (requires hours, optional reason)
    - get: Get current time information
    - set: Set specific time (requires hours for time of day)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    state = session.state

    if action == "advance":
        if hours is None:
            return {"error": "hours required for advance action"}
        state.game_time += hours
        # Handle day rollover
        while state.game_time >= 24:
            state.game_time -= 24
            state.game_day += 1
        await db.update_player_state(session_id, state)

        time_of_day = "night" if state.game_time < 6 or state.game_time >= 20 else \
                      "morning" if state.game_time < 12 else \
                      "afternoon" if state.game_time < 18 else "evening"

        return {
            "success": True,
            "action": "advance",
            "hours_passed": hours,
            "reason": reason,
            "current_time": state.game_time,
            "current_day": state.game_day,
            "time_of_day": time_of_day
        }

    elif action == "get":
        time_of_day = "night" if state.game_time < 6 or state.game_time >= 20 else \
                      "morning" if state.game_time < 12 else \
                      "afternoon" if state.game_time < 18 else "evening"
        return {
            "success": True,
            "action": "get",
            "current_time": state.game_time,
            "current_day": state.game_day,
            "time_of_day": time_of_day
        }

    elif action == "set":
        if hours is None:
            return {"error": "hours required for set action"}
        state.game_time = hours % 24
        await db.update_player_state(session_id, state)
        return {"success": True, "action": "set", "current_time": state.game_time}

    else:
        return {"error": f"Unknown action: {action}. Valid actions: advance, get, set"}


@mcp.tool()
async def manage_faction(
    session_id: str,
    action: str,
    faction_id: str | None = None,
    faction_data: dict | None = None
) -> dict:
    """
    Modular tool for faction and reputation management.

    Actions:
    - create: Create new faction (requires faction_data with: name, description, initial_reputation?)
    - update_reputation: Modify faction reputation (requires faction_id and faction_data with: change, reason?)
    - list: List all factions with reputation levels
    - get: Get specific faction details (requires faction_id)
    - delete: Delete faction (requires faction_id)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not faction_data:
            return {"error": "faction_data required for create action"}
        fac_id = faction_data.get("id", f"faction_{uuid.uuid4().hex[:8]}")
        faction = Faction(
            id=fac_id,
            session_id=session_id,
            name=faction_data["name"],
            description=faction_data["description"],
            reputation=faction_data.get("initial_reputation", 0),
            properties=faction_data.get("properties", {})
        )
        await db.add_faction(faction)
        return {"success": True, "action": "create", "faction_id": fac_id}

    elif action == "update_reputation":
        if not faction_id:
            return {"error": "faction_id required for update_reputation action"}
        if not faction_data or "change" not in faction_data:
            return {"error": "faction_data with 'change' field required"}
        faction = await db.get_faction(faction_id)
        if not faction:
            return {"error": f"Faction {faction_id} not found"}
        old_rep = faction.reputation
        faction.reputation = max(-100, min(100, faction.reputation + faction_data["change"]))
        await db.update_faction(faction)

        # Determine reputation level
        rep_level = "Revered" if faction.reputation > 80 else \
                    "Honored" if faction.reputation > 50 else \
                    "Friendly" if faction.reputation > 20 else \
                    "Neutral" if faction.reputation >= -20 else \
                    "Unfriendly" if faction.reputation >= -50 else \
                    "Hostile" if faction.reputation >= -80 else "Hated"

        return {
            "success": True,
            "action": "update_reputation",
            "faction_id": faction_id,
            "faction_name": faction.name,
            "old_reputation": old_rep,
            "new_reputation": faction.reputation,
            "reputation_level": rep_level,
            "reason": faction_data.get("reason")
        }

    elif action == "list":
        factions = await db.list_factions(session_id)
        return {
            "success": True,
            "action": "list",
            "factions": [{"id": f.id, "name": f.name, "reputation": f.reputation} for f in factions]
        }

    elif action == "get":
        if not faction_id:
            return {"error": "faction_id required for get action"}
        faction = await db.get_faction(faction_id)
        if not faction:
            return {"error": f"Faction {faction_id} not found"}
        return {"success": True, "action": "get", "data": faction.model_dump()}

    elif action == "delete":
        if not faction_id:
            return {"error": "faction_id required for delete action"}
        await db.delete_faction(faction_id)
        return {"success": True, "action": "delete", "faction_id": faction_id}

    else:
        return {"error": f"Unknown action: {action}. Valid actions: create, update_reputation, list, get, delete"}


@mcp.tool()
async def manage_economy(
    session_id: str,
    action: str,
    amount: int | None = None,
    item_id: str | None = None,
    details: dict | None = None
) -> dict:
    """
    Modular tool for economy and item transfer operations.

    Actions:
    - add_currency: Add money to player (requires amount, optional reason in details)
    - remove_currency: Remove money from player (requires amount, optional reason in details)
    - get_balance: Get current currency balance
    - buy_item: Purchase item (requires item_id and amount as cost)
    - sell_item: Sell item (requires item_id and amount as price)
    - transfer_item: Move item between locations (requires item_id and details with: from_location, to_location)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    state = session.state

    if action == "add_currency":
        if amount is None:
            return {"error": "amount required for add_currency action"}
        state.currency += amount
        await db.update_player_state(session_id, state)
        return {
            "success": True,
            "action": "add_currency",
            "amount": amount,
            "new_balance": state.currency,
            "reason": details.get("reason") if details else None
        }

    elif action == "remove_currency":
        if amount is None:
            return {"error": "amount required for remove_currency action"}
        if state.currency < amount:
            return {"error": f"Insufficient funds. Have: {state.currency}, need: {amount}"}
        state.currency -= amount
        await db.update_player_state(session_id, state)
        return {
            "success": True,
            "action": "remove_currency",
            "amount": amount,
            "new_balance": state.currency,
            "reason": details.get("reason") if details else None
        }

    elif action == "get_balance":
        adventure = await db.get_adventure(session.adventure_id)
        currency_name = adventure.currency_config.name if adventure else "gold"
        return {
            "success": True,
            "action": "get_balance",
            "balance": state.currency,
            "currency_name": currency_name
        }

    elif action == "buy_item":
        if not item_id or amount is None:
            return {"error": "item_id and amount (cost) required for buy_item action"}
        if state.currency < amount:
            return {"error": f"Cannot afford item. Have: {state.currency}, cost: {amount}"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        state.currency -= amount
        item.location = None  # Move to player inventory
        await db.update_item(item)
        await db.update_player_state(session_id, state)
        return {
            "success": True,
            "action": "buy_item",
            "item_name": item.name,
            "cost": amount,
            "new_balance": state.currency
        }

    elif action == "sell_item":
        if not item_id or amount is None:
            return {"error": "item_id and amount (price) required for sell_item action"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        state.currency += amount
        await db.delete_item(item_id)  # Remove from game
        await db.update_player_state(session_id, state)
        return {
            "success": True,
            "action": "sell_item",
            "item_name": item.name,
            "price": amount,
            "new_balance": state.currency
        }

    elif action == "transfer_item":
        if not item_id or not details:
            return {"error": "item_id and details (from_location, to_location) required"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        item.location = details.get("to_location")
        await db.update_item(item)
        return {
            "success": True,
            "action": "transfer_item",
            "item_name": item.name,
            "from": details.get("from_location"),
            "to": details.get("to_location")
        }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: add_currency, remove_currency, get_balance, buy_item, sell_item, transfer_item"}


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
