import pytest
from unittest.mock import MagicMock, patch
from adventure_handler.models import Adventure, StatDefinition, WordList, PlayerState, GameSession
from adventure_handler.server import (
    list_adventures,
    start_adventure,
    take_action,
    modify_hp,
    db as server_db
)

# We need to patch the global 'db' object in server.py
# Since 'db' is instantiated at module level, we can patch it.

@pytest.fixture
def mock_db():
    mock = MagicMock()
    # Async methods need to return awaitables (Futures) or be AsyncMock
    # But since we are using MagicMock, we can configure return values to be awaitable if needed,
    # OR better, use AsyncMock if available (Python 3.8+).
    from unittest.mock import AsyncMock
    return AsyncMock()

@pytest.mark.asyncio
async def test_list_adventures(mock_db):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.list_adventures.return_value = [{"id": "adv1", "title": "Test"}]
        result = await list_adventures.fn()
        assert len(result) == 1
        assert result[0]["id"] == "adv1"

@pytest.mark.asyncio
async def test_start_adventure_success(mock_db):
    with patch("adventure_handler.server.db", mock_db):
        # Setup mock returns
        adventure = Adventure(
            id="adv1",
            title="Test",
            description="Desc",
            prompt="Prompt",
            stats=[StatDefinition(name="Str", description="Strength")],
            initial_location="Start",
            initial_story="Story",
            word_lists=[]
        )
        mock_db.get_adventure.return_value = adventure
        mock_db.create_session.return_value = True
        
        # Mock get_session to return the newly created session
        # We need a fake session object
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Start",
                stats={"Str": 10}
            )
        )
        mock_db.get_session.return_value = session

        result = await start_adventure.fn(adventure_id="adv1")
        
        assert "session_id" in result
        assert result["title"] == "Test"
        assert result["location"] == "Start"
        
        # Verify DB calls
        mock_db.create_session.assert_called_once()

@pytest.mark.asyncio
async def test_take_action(mock_db):
    with patch("adventure_handler.server.db", mock_db):
        # Setup session
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Start",
                stats={"Str": 10}
            )
        )
        mock_db.get_session.return_value = session
        
        # Test action without stat check
        result = await take_action.fn(session_id="sess1", action="Look around")
        assert result["success"] is True
        assert result["action"] == "Look around"
        
        # Test action with stat check
        # We need to mock stat_check from dice.py likely, OR rely on logic.
        # The server imports stat_check from .dice.
        # We can patch it there.
        
        with patch("adventure_handler.server.stat_check") as mock_stat_check:
            mock_stat_check.return_value.success = True
            mock_stat_check.return_value.model_dump.return_value = {"success": True}
            
            result = await take_action.fn(session_id="sess1", action="Lift rock", stat_name="Str")
            assert result["success"] is True
            mock_stat_check.assert_called()

@pytest.mark.asyncio
async def test_modify_hp(mock_db):
    with patch("adventure_handler.server.db", mock_db):
        # Setup session
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Start",
                stats={},
                hp=5,
                max_hp=10
            )
        )
        mock_db.get_session.return_value = session
        
        # Heal
        result = await modify_hp.fn(session_id="sess1", amount=3)
        assert result["new_hp"] == 8
        assert result["change"] == 3
        assert session.state.hp == 8 # Should update the object too
        
        mock_db.update_player_state.assert_called_once()
