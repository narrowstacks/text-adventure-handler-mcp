"""FastMCP server for text adventure handler."""
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Annotated

from fastmcp import FastMCP
from fastmcp.resources import Resource
from pydantic import BeforeValidator

from .database import AdventureDB
from .json_validator import json_or_dict_validator
from .models import Adventure, StatDefinition, WordList, Character, Location, Item, InventoryItem, QuestStatus, Memory, StatusEffect, Faction
from .dice import stat_check
from .dice import roll_check as dice_roll_check
from .randomizer import get_random_word, generate_word_prompt, process_template

# Type alias for JSON-validated dictionary parameters
JsonDict = Annotated[Optional[dict], BeforeValidator(json_or_dict_validator)]

# Initialize FastMCP server
mcp = FastMCP("Text Adventure Handler MCP")
db = AdventureDB()

@mcp.tool()
async def initial_instructions() -> dict:
    """
    Call this FIRST. Returns the required workflow, rules, and current adventure catalog.
    Do not improvise until you read this payload; it tells you how to run the session.
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
    Retrieve enforceable rules. Use this to refresh constraints mid-session.
    Hidden sections ('welcome','drop_context','workflow','features','available_adventures') are blocked.

    Args:
        section_name: Optional specific section (e.g., "guidelines_and_rules"); omit to fetch all allowed.
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
    Private log for your next move—never show to the user. Use before pivoting tone/plot.

    Args:
        session_id: Target session.
        thought: Brief internal assessment vs important_rules and memories.
        story_status: "on_track" | "off_rails" | "user_deviating" | "completed" | "stalled".
        plan: Concrete next steps and tool calls.
        user_behavior: "cooperative" | "creative" | "disruptive" | "cheating".
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
    Chain multiple ACTION-ONLY tool calls—no narration between them. Use to apply mechanical updates quickly.
    Reject if any command needs your prose. Ensure commands are non-conflicting and linear.


    Args:
        session_id: The game session
        commands: List of commands, e.g. [{"tool": "move_to_location", "args": {"location": "North"}}]

    Allowed tools:
    - take_action, combat_round
    - manage_inventory, modify_state
    - update_quest, interact_npc, record_event, add_character_memory
    - manage_character, manage_location, manage_item
    - manage_status_effect, manage_time, manage_faction, manage_economy, manage_summary
    """
    # Map string names to actual tool functions
    # Note: We refer to the functions available in this module's scope
    tool_map = {
        "take_action": take_action,
        "combat_round": combat_round,
        "manage_inventory": manage_inventory,
        "modify_state": modify_state,
        "update_quest": update_quest,
        "interact_npc": interact_npc,
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
            # FastMCP tools are callable wrappers, but we need the underlying function
            func = tool_map[tool_name]
            if hasattr(func, "fn"):
                 result = await func.fn(**args)
            else:
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
    """Quick catalog of adventures. Call before start_adventure to pick a valid id."""
    return await db.list_adventures()


@mcp.tool()
async def list_sessions(limit: int = 20) -> list[dict]:
    """
    List recent sessions to resume. Use this instead of guessing a session_id.
    """
    return await db.list_sessions(limit)


@mcp.tool()
async def generate_initial_content(adventure_id: str) -> dict:
    """
    Use when you want to replace the canned opening. Returns a strict JSON prompt so YOU can author
    the opening story, locations, and NPCs. After generating, you MUST call start_adventure with
    generated_story / generated_characters / generated_locations.
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
    Resume an existing session. Use immediately after list_sessions to pull live state and history.
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
    custom_stats: JsonDict = None,
    generated_story: str = None,
    generated_locations: list[dict] = None,
    generated_characters: list[dict] = None,
) -> dict:
    """
    Single entry point to launch a session. Use ONLY after picking adventure_id (or generating custom content).
    Returns session_id and initial state you must echo back to the user.

    Args:
        adventure_id: Required.
        randomize_initial: Leave True unless you need deterministic templates.
        character_name: Optional player name to store.
        roll_stats/custom_stats: Choose one path for stat setup.
        generated_story/locations/characters: Pass outputs you authored via generate_initial_content.
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
    One-stop status fetch. Prefer this over piecemeal state/history/memory calls.

    Args:
        include_* flags: Turn on only what you need; keep payload lean.
        include_character_memories: Pass a name to pull their top memories.
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
    Log a player action and resolve an optional check. Call this for narrative actions that may fail.
    You narrate the outcome using the returned success flag and dice_roll—do not invent a roll yourself.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    # Perform dice check if stat is used
    if stat_name:
        # Case-insensitive lookup
        stat_key = next((k for k in session.state.stats.keys() if k.lower() == stat_name.lower()), None)
        
        if not stat_key:
            return {"error": f"Stat '{stat_name}' not found in this adventure"}

        stat_value = session.state.stats[stat_key]
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
    score_delta = 10 if success else 0
    session.state.score += score_delta
    await db.update_player_state(session_id, session.state)

    await db.add_action(
        session_id, 
        action_record, 
        "Success" if success else "Failure", 
        score_delta,
        dice_roll=roll_result.model_dump() if roll_result else None
    )

    return {
        "session_id": session_id,
        "action": action,
        "success": success,
        "dice_roll": roll_result.model_dump() if roll_result else None,
        "score_change": score_delta,
        "new_score": session.state.score,
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
    Run a single player attack turn. Use this instead of hand-waving combat math.
    After you get the result, narrate the exchange and adjust player HP via modify_state if counter-attack hits.

    Args:
        player_action: Plain description of the attack.
        attack_stat/target_ac/damage_dice: Required to resolve the roll.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    # Case-insensitive lookup
    stat_key = next((k for k in session.state.stats.keys() if k.lower() == attack_stat.lower()), None)
    
    if not stat_key:
        return {"error": f"Stat '{attack_stat}' not found"}

    # Player Attack
    stat_value = session.state.stats[stat_key]
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
        "prompt": f"Describe the combat round. Player {message}. Then describe {target_name}'s counter-attack and specify damage to player using modify_state(action=\"hp\", value=-damage) if needed."
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
    Strict quest control. Start a quest by providing title, or update status/objectives on an existing id.
    Use this whenever objectives shift; do not track quests in free text.
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
    Adjust NPC relationship score. sentiment_change must reflect the last interaction; negative for harm.
    Do not narrate here—follow up with dialogue in the main reply.
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
async def roll_check(session_id: str, stat_name: str = None, difficulty_class: int = 10) -> dict:
    """Quick d20/stat check. Call before risky moves; don't fake probabilities."""
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if stat_name:
        # Case-insensitive lookup
        stat_key = next((k for k in session.state.stats.keys() if k.lower() == stat_name.lower()), None)
        
        if not stat_key:
            return {"error": f"Stat '{stat_name}' not found"}
        stat_value = session.state.stats[stat_key]
        result = stat_check(stat_value, difficulty_class)
    else:
        result = dice_roll_check(difficulty_class=difficulty_class)

    return result.model_dump()


@mcp.tool()
async def modify_state(
    session_id: str,
    action: str,
    value: int | str = None,
    stat_name: str = None,
    reason: str = None
) -> dict:
    """
    The ONLY tool for HP, stat, score, or location changes. Call immediately after outcomes—never edit state in prose.

    Actions:
    - hp: Heal/damage (int). Provide reason when possible.
    - stat: Adjust named stat by int delta.
    - score: Add/subtract points.
    - location: Move player to a named location string.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    # Attempt to coerce numeric string values for numeric actions
    if action in ["hp", "stat", "score"] and isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            # If conversion fails, we leave it as string and let the specific action handlers return their error messages
            pass

    if action == "hp":
        if value is None:
            return {"error": "value required for hp action (amount to heal/damage)"}
        if not isinstance(value, int):
            return {"error": "value must be an integer for hp action"}

        old_hp = session.state.hp
        new_hp = session.state.hp + value
        new_hp = max(0, min(session.state.max_hp, new_hp))

        session.state.hp = new_hp
        await db.update_player_state(session_id, session.state)

        return {
            "success": True,
            "action": "hp",
            "old_hp": old_hp,
            "new_hp": new_hp,
            "change": value,
            "reason": reason,
            "status": "Unconscious/Dead" if new_hp == 0 else "Alive"
        }

    elif action == "stat":
        if not stat_name:
            return {"error": "stat_name required for stat action"}
        if value is None:
            return {"error": "value required for stat action (amount to change)"}
        if not isinstance(value, int):
            return {"error": "value must be an integer for stat action"}

        # Case-insensitive lookup
        stat_key = next((k for k in session.state.stats.keys() if k.lower() == stat_name.lower()), None)

        if not stat_key:
            return {"error": f"Stat '{stat_name}' not found"}

        adventure = await db.get_adventure(session.adventure_id)
        stat_def = next((s for s in adventure.stats if s.name.lower() == stat_key.lower()), None)

        old_value = session.state.stats[stat_key]
        new_value = old_value + value

        # Clamp to stat bounds
        if stat_def:
            new_value = max(stat_def.min_value, min(stat_def.max_value, new_value))
        else:
            new_value = max(0, min(20, new_value))

        session.state.stats[stat_key] = new_value
        await db.update_player_state(session_id, session.state)

        return {
            "success": True,
            "action": "stat",
            "stat": stat_key,
            "old_value": old_value,
            "new_value": new_value,
            "change": value,
        }

    elif action == "score":
        if value is None:
            return {"error": "value required for score action (points to add/subtract)"}
        if not isinstance(value, int):
            return {"error": "value must be an integer for score action"}

        old_score = session.state.score
        session.state.score += value
        await db.update_player_state(session_id, session.state)

        return {
            "success": True,
            "action": "score",
            "old_score": old_score,
            "new_score": session.state.score,
            "change": value
        }

    elif action == "location":
        if value is None:
            return {"error": "value required for location action (new location name)"}
        if not isinstance(value, str):
            return {"error": "value must be a string for location action"}

        old_location = session.state.location
        session.state.location = value
        await db.update_player_state(session_id, session.state)

        return {
            "success": True,
            "action": "location",
            "old_location": old_location,
            "new_location": value,
            "message": f"Moved to {value}"
        }

    else:
        return {"error": f"Unknown action: {action}. Valid actions: hp, stat, score, location"}


@mcp.tool()
async def manage_inventory(
    session_id: str,
    action: str,
    item_name: str = None,
    quantity: int = 1,
    properties: JsonDict = None
) -> dict:
    """
    Single inventory authority. Use instead of freeform text edits.

    Actions:
    - add/remove/update/check/list/use — supply item_name where required; respect quantities; mark consumables via properties.
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
async def randomize_word(
    session_id: str,
    word_list_name: str,
    category_name: str = None,
    use_predefined: bool = True,
) -> dict:
    """
    Pull a random word from the adventure lists (preferred) or get a prompt to generate one.
    Use for flavor, naming, and template fills. Choose category to stay on-theme.
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
    Maintain concise session summaries. Create after major beats; fetch for recaps instead of rereading history.

    Actions: create | get | get_latest | delete.
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

        await db.delete_session_summary(summary_id)
        return {
            "success": True,
            "action": "delete",
            "summary_id": summary_id,
            "message": "Summary deleted successfully"
        }

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
    Mandatory after any public, notable event. Writes memories to all witnesses at the location.
    Keep description tight but complete; tag it for future recall (e.g., ["hostile","magic"]).
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
    Plant a targeted memory in one NPC (whisper, rumor, note). Do NOT use for public events—use record_event instead.
    Type: observation | interaction | rumor. Keep wording short and factual.
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
    character_data: JsonDict = None
) -> dict:
    """
    Manage NPCs and Characters with full CRUD operations. Characters bring your adventure world to life.

    Args:
        session_id: The game session ID
        action: Operation to perform - "create", "read", "update", "delete", or "list"
        character_id: Required for read/update/delete operations. The unique ID of the character.
        character_data: Required for create/update. Can be a dictionary or JSON string.

    Actions:
        - "create": Add a new NPC to the game world
        - "read": Get details of a specific character
        - "update": Modify an existing character
        - "delete": Remove a character from the game
        - "list": Get all characters in the session

    Character Data Structure:
        {
            "name": str,              # Required - The character's name (e.g., "Gandalf")
            "description": str,       # Required - Physical/personality description
            "location": str,          # Required - ID of starting location
            "stats": dict,            # Optional - Character stats (e.g., {"hp": 10, "str": 12})
            "properties": dict        # Optional - Custom properties (e.g., {"is_merchant": true, "faction": "rebels"})
        }

    Examples:
        # Create a new NPC
        manage_character(
            session_id="abc123",
            action="create",
            character_data={
                "name": "Elder Thorne",
                "description": "An ancient wizard with a long white beard and piercing blue eyes.",
                "location": "wizard_tower",
                "stats": {"hp": 50, "magic": 20},
                "properties": {"is_quest_giver": true, "knows_ancient_magic": true}
            }
        )

        # Update a character
        manage_character(
            session_id="abc123",
            action="update",
            character_id="char_12345",
            character_data={
                "location": "tavern",
                "description": "The wizard looks tired and disheveled.",
                "stats": {"hp": 25}
            }
        )

        # List all characters
        manage_character(session_id="abc123", action="list")

    Returns:
        Dictionary with success status and relevant data based on action
    """
    # JSON strings are automatically parsed by the JsonDict type annotation
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not character_data:
            return {"error": "character_data required for create action. Please provide a dictionary with 'name', 'description', and 'location' fields."}
        if not isinstance(character_data, dict):
            return {"error": "character_data must be a dictionary after parsing. Got type: " + str(type(character_data))}

        required_fields = ["name", "description", "location"]
        missing = [f for f in required_fields if f not in character_data or not character_data[f]]
        if missing:
            return {"error": f"Missing required fields in character_data: {', '.join(missing)}. All of 'name', 'description', and 'location' must be non-empty strings."}

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
            return {"error": "character_data required for update action. Please provide fields to update."}
        if not isinstance(character_data, dict):
            return {"error": "character_data must be a dictionary after parsing. Got type: " + str(type(character_data))}
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
    location_data: JsonDict = None
) -> dict:
    """
    Manage game locations with full CRUD operations. Locations form the world map of your adventure.

    Args:
        session_id: The game session ID
        action: Operation to perform - "create", "read", "update", "delete", or "list"
        location_id: Required for read/update/delete operations. The unique ID of the location.
        location_data: Required for create/update. Can be a dictionary or JSON string.

    Actions:
        - "create": Add a new location to the game world
        - "read": Get details of a specific location
        - "update": Modify an existing location
        - "delete": Remove a location from the game
        - "list": Get all locations in the session

    Location Data Structure:
        {
            "name": str,              # Required - The location name (e.g., "Dark Forest")
            "description": str,       # Required - Detailed description of the location
            "connected_to": list,     # Optional - List of location IDs this connects to
            "properties": dict        # Optional - Custom properties (e.g., {"locked": true, "hidden": false})
        }

    Examples:
        # Create a new location
        manage_location(
            session_id="abc123",
            action="create",
            location_data={
                "name": "Pawnbroker's Shop",
                "description": "A cluttered shop filled with curious items. The owner, Mr. Verris, eyes you suspiciously.",
                "connected_to": ["town_square", "back_alley"],
                "properties": {"shop_type": "pawnbroker", "owner": "Mr. Verris"}
            }
        )

        # Update a location
        manage_location(
            session_id="abc123",
            action="update",
            location_id="loc_12345",
            location_data={
                "description": "The shop is now empty, Mr. Verris has fled.",
                "properties": {"abandoned": true}
            }
        )

        # List all locations
        manage_location(session_id="abc123", action="list")

    Returns:
        Dictionary with success status and relevant data based on action
    """
    # JSON strings are automatically parsed by the JsonDict type annotation
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not location_data:
            return {"error": "location_data required for create action. Please provide a dictionary with 'name' and 'description' fields."}
        if not isinstance(location_data, dict):
            return {"error": "location_data must be a dictionary after parsing. Got type: " + str(type(location_data))}
        missing = [f for f in ["name", "description"] if f not in location_data or not location_data[f]]
        if missing:
            return {"error": f"Missing required fields in location_data: {', '.join(missing)}. Both 'name' and 'description' must be non-empty strings."}
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
            return {"error": "location_data required for update action. Please provide fields to update."}
        if not isinstance(location_data, dict):
            return {"error": "location_data must be a dictionary after parsing. Got type: " + str(type(location_data))}
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
    item_data: JsonDict = None
) -> dict:
    """
    Manage game items with full CRUD operations. Items can exist in locations or player inventory.

    Args:
        session_id: The game session ID
        action: Operation to perform - "create", "read", "update", "delete", or "list"
        item_id: Required for read/update/delete operations. The unique ID of the item.
        item_data: Required for create/update. Can be a dictionary or JSON string.

    Actions:
        - "create": Add a new item to the game world
        - "read": Get details of a specific item
        - "update": Modify an existing item
        - "delete": Remove an item from the game
        - "list": Get all items in the session

    Item Data Structure:
        {
            "name": str,              # Required - The item name (e.g., "Magic Sword")
            "description": str,       # Required - Detailed description of the item
            "location": str,          # Optional - Location ID where item is found
            "in_inventory": bool,     # Optional - True if in player inventory
            "properties": dict        # Optional - Custom properties (e.g., {"damage": 10, "magical": true})
        }

    Examples:
        # Create a new item in a location
        manage_item(
            session_id="abc123",
            action="create",
            item_data={
                "name": "Ancient Tome",
                "description": "A dusty book with strange symbols on the cover.",
                "location": "library",
                "properties": {"readable": true, "language": "elvish"}
            }
        )

        # Create an item in player inventory
        manage_item(
            session_id="abc123",
            action="create",
            item_data={
                "name": "Health Potion",
                "description": "A red liquid that restores health.",
                "in_inventory": true,
                "properties": {"consumable": true, "healing": 20}
            }
        )

        # Update an item
        manage_item(
            session_id="abc123",
            action="update",
            item_id="item_12345",
            item_data={
                "description": "The tome now glows with magical energy.",
                "properties": {"activated": true}
            }
        )

    Returns:
        Dictionary with success status and relevant data based on action
    """
    # JSON strings are automatically parsed by the JsonDict type annotation
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    if action == "create":
        if not item_data:
            return {"error": "item_data required for create action. Please provide a dictionary with 'name' and 'description' fields."}
        if not isinstance(item_data, dict):
            return {"error": "item_data must be a dictionary after parsing. Got type: " + str(type(item_data))}
        missing = [f for f in ["name", "description"] if f not in item_data or not item_data[f]]
        if missing:
            return {"error": f"Missing required fields in item_data: {', '.join(missing)}. Both 'name' and 'description' must be non-empty strings."}
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
            return {"error": "item_data required for update action. Please provide fields to update."}
        if not isinstance(item_data, dict):
            return {"error": "item_data must be a dictionary after parsing. Got type: " + str(type(item_data))}
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
    effect_data: JsonDict = None
) -> dict:
    """
    Control status effects. Apply/remove/list/update instead of ad-hoc narration.

    Args:
        session_id: The game session ID
        action: Operation to perform - "apply", "remove", "list", "update", or "tick"
        effect_id: The ID of the status effect (for remove/update operations)
        effect_data: Effect details as dictionary or JSON string

    Provide duration and modifiers when applying; tick or alter via update as time passes.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)
    if not adventure or not adventure.features.status_effects:
        return {"error": "Status effects feature is disabled for this adventure"}

    if action == "apply":
        if not effect_data:
            return {"error": "effect_data required for apply action"}
        missing = [f for f in ["name", "description", "duration"] if f not in effect_data or effect_data[f] in [None, ""]]
        if missing:
            return {"error": f"Missing required fields in effect_data: {', '.join(missing)}"}
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
    Authoritative clock control. Advance after travel/rest; never skip day rollover.
    Actions: advance | get | set. Provide reason when advancing to track pacing.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)
    if not adventure or not adventure.features.time_tracking:
        return {"error": "Time tracking is disabled for this adventure"}

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
    faction_data: JsonDict = None
) -> dict:
    """
    Govern factions and reputation. Use update_reputation whenever player actions shift standing.

    Args:
        session_id: The game session ID
        action: Operation to perform - "create", "update_reputation", "list", "get", or "delete"
        faction_id: The ID of the faction (for update/get/delete operations)
        faction_data: Faction details as dictionary or JSON string

    Actions: create | update_reputation | list | get | delete.
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)
    if not adventure or not adventure.features.factions:
        return {"error": "Factions feature is disabled for this adventure"}

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
    details: JsonDict = None
) -> dict:
    """
    Enforce currency and trades. Never adjust money in prose—use this.

    Args:
        session_id: The game session ID
        action: The economy action to perform
        amount: The amount of currency (for add/remove/buy/sell actions)
        item_id: The ID of the item (for buy/sell/transfer actions)
        details: Additional details as dictionary or JSON string (e.g., {"reason": "Payment from quest"})

    Actions:
    - add_currency / remove_currency (with reason when possible)
    - get_balance
    - buy_item / sell_item (use costs; respects balance)
    - transfer_item (between locations)
    """
    session = await db.get_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}

    adventure = await db.get_adventure(session.adventure_id)
    if not adventure or not adventure.features.currency:
        return {"error": "Currency/economy is disabled for this adventure"}

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
        if amount < 0:
            return {"error": "amount must be positive for buy_item"}
        if state.currency < amount:
            return {"error": f"Cannot afford item. Have: {state.currency}, cost: {amount}"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        if item.session_id != session_id:
            return {"error": "Item does not belong to this session"}
        if item.location is None:
            return {"error": "Item is not available for purchase"}

        # Move item into player inventory
        existing = next((i for i in state.inventory if i.id == item_id or i.name == item.name), None)
        if existing:
            existing.quantity += 1
        else:
            state.inventory.append(
                InventoryItem(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    quantity=1,
                    properties=item.properties,
                )
            )

        state.currency -= amount
        await db.delete_item(item_id)  # Remove world item record
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
        if amount < 0:
            return {"error": "amount must be positive for sell_item"}

        # Ensure player owns the item
        inv_item = next((i for i in state.inventory if i.id == item_id), None)
        if not inv_item:
            return {"error": f"Item {item_id} not found in player inventory"}

        sold_qty = 1
        if inv_item.quantity > 1:
            inv_item.quantity -= 1
        else:
            state.inventory.remove(inv_item)
        state.currency += amount
        await db.update_player_state(session_id, state)
        return {
            "success": True,
            "action": "sell_item",
            "item_name": inv_item.name,
            "price": amount,
            "quantity_sold": sold_qty,
            "new_balance": state.currency
        }

    elif action == "transfer_item":
        if not item_id or not details:
            return {"error": "item_id and details (from_location, to_location) required"}
        item = await db.get_item(item_id)
        if not item:
            return {"error": f"Item {item_id} not found"}
        if item.session_id != session_id:
            return {"error": "Item does not belong to this session"}
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
