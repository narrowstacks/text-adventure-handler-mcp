import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from adventure_handler.server import modify_state
from adventure_handler.models import GameSession, PlayerState, Adventure

@pytest.mark.asyncio
async def test_modify_state_hp_string_input_bug():
    """
    Test that providing a string 'value' to modify_state for 'hp' action
    fails if not cast to int.
    """
    # Mock session and state
    session_id = "test_session"
    mock_state = PlayerState(
        session_id=session_id,
        hp=10,
        max_hp=20,
        location="Start",
        stats={"strength": 10}
    )
    mock_session = GameSession(
        id=session_id,
        adventure_id="adv1",
        created_at=datetime.now(),
        last_played=datetime.now(),
        state=mock_state
    )

    # Patch the db instance in server.py
    # Since we import modify_state from adventure_handler.server, 
    # we must patch adventure_handler.server.db
    with patch("adventure_handler.server.db") as mock_db:
        mock_db.get_session = AsyncMock(return_value=mock_session)
        mock_db.update_player_state = AsyncMock()
        # Minimal adventure mock
        mock_db.get_adventure = AsyncMock(return_value=Adventure(
            id="adv1", title="Test", description="Desc", prompt="Prompt",
            stats=[], word_lists=[], initial_location="Loc", initial_story="Story"
        ))

        # Call with string value "-3"
        result = await modify_state.fn(
            session_id=session_id,
            action="hp",
            value="-3",
            reason="Test damage"
        )

        # We expect success now
        assert result.get("success") is True
        assert result["change"] == -3
        assert result["new_hp"] == 7

@pytest.mark.asyncio
async def test_modify_state_hp_invalid_string():
    """
    Test that providing a non-numeric string 'value' still returns error.
    """
    session_id = "test_session_invalid"
    mock_state = PlayerState(
        session_id=session_id,
        hp=10,
        max_hp=20,
        location="Start",
        stats={}
    )
    mock_session = GameSession(
        id=session_id,
        adventure_id="adv1",
        created_at=datetime.now(),
        last_played=datetime.now(),
        state=mock_state
    )

    with patch("adventure_handler.server.db") as mock_db:
        mock_db.get_session = AsyncMock(return_value=mock_session)
        
        result = await modify_state.fn(
            session_id=session_id,
            action="hp",
            value="not-a-number",
            reason="Test"
        )
        
        assert "error" in result
        assert result["error"] == "value must be an integer for hp action"