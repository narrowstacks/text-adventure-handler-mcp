import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from adventure_handler.database import AdventureDB
from adventure_handler.models import Character, Memory, Adventure
from adventure_handler.server import record_event, get_session_info, add_character_memory, db as server_db
from unittest.mock import patch

@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "memory_test.db"
    database = AdventureDB(db_path=str(db_path))
    await database.init_db()
    return database

@pytest.fixture
def sample_character():
    return Character(
        id=str(uuid.uuid4()),
        session_id="sess1",
        name="Witness NPC",
        description="A bystander",
        location="Town Square",
        stats={},
        properties={}
    )

@pytest.mark.asyncio
async def test_memory_persistence(test_db, sample_character):
    """Test that memories are saved and loaded from DB."""
    # Add character
    await test_db.add_character(sample_character)
    
    # Add memory manually
    memory = Memory(
        id="mem1",
        description="Saw a bird",
        timestamp=datetime.now(),
        type="observation",
        importance=1
    )
    sample_character.memories.append(memory)
    await test_db.update_character(sample_character)
    
    # Retrieve
    fetched = await test_db.get_character(sample_character.id)
    assert len(fetched.memories) == 1
    assert fetched.memories[0].description == "Saw a bird"

@pytest.mark.asyncio
async def test_record_event_tool(test_db):
    """Test the record_event tool logic."""
    # Setup
    with patch("adventure_handler.server.db", test_db):
        # Create session and chars
        adv = Adventure(
            id="adv1", title="T", description="D", prompt="P", stats=[], initial_location="Town Square", initial_story="S", word_lists=[]
        )
        await test_db.add_adventure(adv)
        await test_db.create_session("sess1", "adv1")
        
        # Add 2 chars, one in location, one outside
        char1 = Character(id="c1", session_id="sess1", name="Witness", location="Town Square", description="D")
        char2 = Character(id="c2", session_id="sess1", name="Absent", location="Forest", description="D")
        await test_db.add_character(char1)
        await test_db.add_character(char2)
        
        # Record event
        result = await record_event.fn(session_id="sess1", event_description="Explosion", location="Town Square", importance=5)
        
        assert result["witness_count"] == 1
        assert "Witness" in result["witnesses"]
        
        # Verify memory using get_session_info with include_character_memories
        c1_info = await get_session_info.fn(session_id="sess1", include_state=False, include_character_memories="Witness")
        assert len(c1_info["character_memories"]["memories"]) == 1
        assert c1_info["character_memories"]["memories"][0]["description"] == "Explosion"
        assert c1_info["character_memories"]["memories"][0]["importance"] == 5

        # Verify absent char has no memory
        c2_info = await get_session_info.fn(session_id="sess1", include_state=False, include_character_memories="Absent")
        assert len(c2_info["character_memories"]["memories"]) == 0

@pytest.mark.asyncio
async def test_memory_decay(test_db):
    """Test that memories decay (limit 50)."""
    # Setup
    with patch("adventure_handler.server.db", test_db):
        char = Character(id="c1", session_id="sess1", name="OldGuy", location="Loc", description="D")
        await test_db.add_character(char)
        
        # Add 55 memories
        from adventure_handler.server import _add_memory_to_character
        for i in range(55):
            await _add_memory_to_character(char, f"Event {i}", "observation", importance=1)
            
        # Fetch
        fetched = await test_db.get_character("c1")
        assert len(fetched.memories) == 50
        # Should have forgotten the first ones (0-4)
        descriptions = [m.description for m in fetched.memories]
        assert "Event 0" not in descriptions
        assert "Event 54" in descriptions
