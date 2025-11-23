import pytest
import pytest_asyncio
import json
from datetime import datetime
from adventure_handler.database import AdventureDB
from adventure_handler.models import (
    Adventure,
    StatDefinition,
    WordList,
    PlayerState,
    Action,
    DiceRoll
)


@pytest_asyncio.fixture
async def db(tmp_path):
    """Create a database instance with a temporary file."""
    db_path = tmp_path / "test_adventure.db"
    database = AdventureDB(db_path=str(db_path))
    await database.init_db()
    return database


@pytest.fixture
def sample_adventure():
    return Adventure(
        id="test-adventure",
        title="Test Adventure",
        description="A test adventure",
        prompt="You are testing.",
        stats=[
            StatDefinition(name="Strength", description="Power"),
            StatDefinition(name="Intelligence", description="Smarts")
        ],
        starting_hp=10,
        word_lists=[
            WordList(
                name="enemies",
                description="Bad guys",
                categories={"common": ["goblin", "orc"]}
            )
        ],
        initial_location="Start Room",
        initial_story="You start here."
    )


@pytest.mark.asyncio
async def test_init_db(db):
    """Test database initialization."""
    # Just by using the fixture, init_db is called.
    # We can verify tables exist.
    async with db._get_conn() as conn:
        async with conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
            table_names = [t[0] for t in tables]
            assert "adventures" in table_names
            assert "game_sessions" in table_names
            assert "player_state" in table_names
            assert "action_history" in table_names


@pytest.mark.asyncio
async def test_add_and_get_adventure(db, sample_adventure):
    """Test adding and retrieving an adventure."""
    await db.add_adventure(sample_adventure)
    
    fetched = await db.get_adventure(sample_adventure.id)
    assert fetched is not None
    assert fetched.id == sample_adventure.id
    assert fetched.title == sample_adventure.title
    assert len(fetched.stats) == 2
    assert fetched.stats[0].name == "Strength"
    assert len(fetched.word_lists) == 1
    assert fetched.word_lists[0].categories["common"] == ["goblin", "orc"]


@pytest.mark.asyncio
async def test_create_and_get_session(db, sample_adventure):
    """Test creating and retrieving a game session."""
    await db.add_adventure(sample_adventure)
    session_id = "test-session"
    
    success = await db.create_session(session_id, sample_adventure.id)
    assert success is True
    
    session = await db.get_session(session_id)
    assert session is not None
    assert session.id == session_id
    assert session.adventure_id == sample_adventure.id
    assert session.state.hp == 10
    assert session.state.location == "Start Room"
    assert "Strength" in session.state.stats
    assert session.state.stats["Strength"] == 10


@pytest.mark.asyncio
async def test_update_player_state(db, sample_adventure):
    """Test updating player state."""
    await db.add_adventure(sample_adventure)
    session_id = "test-session"
    await db.create_session(session_id, sample_adventure.id)
    
    session = await db.get_session(session_id)
    state = session.state
    
    # Modify state
    state.hp = 5
    state.location = "New Room"
    state.score = 100
    
    success = await db.update_player_state(session_id, state)
    assert success is True
    
    updated_session = await db.get_session(session_id)
    assert updated_session.state.hp == 5
    assert updated_session.state.location == "New Room"
    assert updated_session.state.score == 100


@pytest.mark.asyncio
async def test_action_history(db, sample_adventure):
    """Test adding and retrieving action history."""
    await db.add_adventure(sample_adventure)
    session_id = "test-session"
    await db.create_session(session_id, sample_adventure.id)
    
    action = Action(
        session_id=session_id,
        action_text="Attack goblin",
        stat_used="Strength",
        difficulty_class=10,
        timestamp=datetime.now()
    )
    
    dice_roll = {"roll": 15, "total": 15, "success": True, "message": "Rolled 15"}
    
    await db.add_action(
        session_id=session_id,
        action=action,
        outcome="You hit the goblin!",
        score_change=10,
        dice_roll=dice_roll
    )
    
    history = await db.get_history(session_id)
    assert len(history) == 1
    assert history[0]["action_text"] == "Attack goblin"
    assert history[0]["outcome"] == "You hit the goblin!"
    assert history[0]["score_change"] == 10
