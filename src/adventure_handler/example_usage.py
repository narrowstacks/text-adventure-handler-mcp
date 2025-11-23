"""
Example usage of the Adventure Handler MCP server.

Run this script to:
1. Initialize the database with sample adventures
2. Create a game session
3. Demonstrate basic operations
"""

from adventure_handler.server import db, load_sample_adventures
from adventure_handler.models import Adventure, StatDefinition


def main():
    print("=" * 60)
    print("AI Adventure Handler - Example Usage")
    print("=" * 60)

    # Load sample adventures
    print("\n[1] Loading sample adventures...")
    load_sample_adventures()
    print("✓ Sample adventures loaded")

    # List adventures
    print("\n[2] Available adventures:")
    adventures = db.list_adventures()
    for adv in adventures:
        print(f"  - {adv['title']} ({adv['id']})")
        print(f"    {adv['description']}")

    # Start a game session
    print("\n[3] Starting a new game session...")
    adventure_id = "fantasy_dungeon"
    session_id = db.create_session("session_demo", adventure_id)
    session = db.get_session("session_demo")

    print(f"✓ Session created: {session_id}")
    print(f"  Adventure: {adventure_id}")
    print(f"  Location: {session.state.location}")
    print(f"  Stats: {session.state.stats}")
    print(f"  Score: {session.state.score}")

    # Demonstrate stat modification
    print("\n[4] Modifying stats...")
    session.state.stats["Strength"] += 2
    db.update_player_state("session_demo", session.state)
    updated = db.get_session("session_demo")
    print(f"✓ Strength increased to: {updated.state.stats['Strength']}")

    # Demonstrate location update
    print("\n[5] Moving to new location...")
    session.state.location = "Crystal Chamber"
    db.update_player_state("session_demo", session.state)
    print(f"✓ Now at: {session.state.location}")

    # Demonstrate inventory
    print("\n[6] Adding items to inventory...")
    session.state.inventory.extend(["Torch", "Healing Potion", "Iron Key"])
    db.update_player_state("session_demo", session.state)
    print(f"✓ Inventory: {session.state.inventory}")

    # Demonstrate score
    print("\n[7] Updating score...")
    session.state.score += 50
    db.update_player_state("session_demo", session.state)
    print(f"✓ New score: {session.state.score}")

    # Demonstrate dice rolls
    print("\n[8] Testing dice rolling...")
    from adventure_handler.dice import roll_check, stat_check

    # Plain d20 roll
    roll1 = roll_check(difficulty_class=12)
    print(f"  D20 check (DC 12): {roll1.message}")

    # Stat-based roll
    roll2 = stat_check(
        stat_value=14, difficulty_class=13
    )  # +2 modifier from 14 stat
    print(f"  Strength check (DC 13): {roll2.message}")

    print("\n[9] Adventure prompt sample:")
    adventure = db.get_adventure(adventure_id)
    print(f"  Title: {adventure.title}")
    print(f"  Prompt preview: {adventure.prompt[:100]}...")

    print("\n[10] Testing python_eval for batch operations...")
    batch_code = """
# Multi-step operation: adventure completion
state.location = "Treasure Chamber"
state.inventory.append("Crystal of Power")
state.stats["Intelligence"] += 1
state.score += 100
_result = {
    "message": "Quest completed!",
    "location": state.location,
    "score": state.score,
    "items": len(state.inventory)
}
"""
    from adventure_handler.server import python_eval
    batch_result = python_eval("session_demo", batch_code)
    print(f"✓ Batch operation result:")
    print(f"  Success: {batch_result.get('success')}")
    if batch_result.get('result'):
        print(f"  Result: {batch_result['result']}")
    print(f"  New state: {batch_result.get('state')}")

    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
