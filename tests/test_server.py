import pytest
from unittest.mock import MagicMock, patch
from adventure_handler.models import Adventure, StatDefinition, WordList, PlayerState, GameSession
from adventure_handler.server import (
    list_adventures,
    start_adventure,
    take_action,
    modify_state,
    skill_check,
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
async def test_take_action_case_insensitive(mock_db):
    """Test that stat lookup works regardless of case."""
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
                stats={"Strength": 10} # Title Case
            )
        )
        mock_db.get_session.return_value = session
        
        with patch("adventure_handler.server.stat_check") as mock_stat_check:
            mock_stat_check.return_value.success = True
            mock_stat_check.return_value.model_dump.return_value = {"success": True}
            
            # Test with lowercase "strength"
            result = await take_action.fn(session_id="sess1", action="Lift rock", stat_name="strength")
            
            # Should NOT return error
            assert "error" not in result
            assert result["success"] is True
            
            # Test with UPPERCASE "STRENGTH"
            result = await take_action.fn(session_id="sess1", action="Lift rock", stat_name="STRENGTH")
            assert "error" not in result
            assert result["success"] is True

@pytest.mark.asyncio
async def test_modify_state_hp(mock_db):
    """Test modify_state with hp action"""
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

        # Heal using modify_state
        result = await modify_state.fn(session_id="sess1", action="hp", value=3)
        assert result["success"] is True
        assert result["action"] == "hp"
        assert result["new_hp"] == 8
        assert result["change"] == 3
        assert session.state.hp == 8 # Should update the object too

        mock_db.update_player_state.assert_called_once()

@pytest.mark.asyncio
async def test_modify_state_score(mock_db):
    """Test modify_state with score action"""
    with patch("adventure_handler.server.db", mock_db):
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
                score=100
            )
        )
        mock_db.get_session.return_value = session

        result = await modify_state.fn(session_id="sess1", action="score", value=50)
        assert result["success"] is True
        assert result["action"] == "score"
        assert result["new_score"] == 150
        assert result["change"] == 50

@pytest.mark.asyncio
async def test_modify_state_location(mock_db):
    """Test modify_state with location action"""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Start",
                stats={}
            )
        )
        mock_db.get_session.return_value = session

        result = await modify_state.fn(session_id="sess1", action="location", value="Town Square")
        assert result["success"] is True
        assert result["action"] == "location"
        assert result["new_location"] == "Town Square"
        assert session.state.location == "Town Square"


# ============ skill_check tests ============

@pytest.mark.asyncio
async def test_skill_check_success(mock_db):
    """Test skill_check when stat meets threshold."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Tavern",
                stats={"Charisma": 15},
                score=0
            )
        )
        mock_db.get_session.return_value = session

        result = await skill_check.fn(
            session_id="sess1",
            action="Persuade the guard to let you pass",
            stat_name="Charisma",
            threshold=12
        )

        assert result["success"] is True
        assert result["stat_name"] == "Charisma"
        assert result["stat_value"] == 15
        assert result["threshold"] == 12
        assert result["margin"] == 3  # 15 - 12
        assert result["score_change"] == 10
        assert result["new_score"] == 10


@pytest.mark.asyncio
async def test_skill_check_failure(mock_db):
    """Test skill_check when stat is below threshold."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Library",
                stats={"Intelligence": 8},
                score=50
            )
        )
        mock_db.get_session.return_value = session

        result = await skill_check.fn(
            session_id="sess1",
            action="Decipher the ancient runes",
            stat_name="Intelligence",
            threshold=14
        )

        assert result["success"] is False
        assert result["stat_value"] == 8
        assert result["threshold"] == 14
        assert result["margin"] == -6  # 8 - 14
        assert result["score_change"] == 0
        assert result["new_score"] == 50  # Unchanged


@pytest.mark.asyncio
async def test_skill_check_exact_threshold(mock_db):
    """Test skill_check when stat exactly matches threshold (should pass)."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Gate",
                stats={"Strength": 14},
                score=0
            )
        )
        mock_db.get_session.return_value = session

        result = await skill_check.fn(
            session_id="sess1",
            action="Force open the rusty door",
            stat_name="Strength",
            threshold=14
        )

        assert result["success"] is True
        assert result["margin"] == 0  # Exactly at threshold


@pytest.mark.asyncio
async def test_skill_check_invalid_stat(mock_db):
    """Test skill_check with non-existent stat returns error."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Start",
                stats={"Strength": 10}
            )
        )
        mock_db.get_session.return_value = session

        result = await skill_check.fn(
            session_id="sess1",
            action="Cast a spell",
            stat_name="Magic",
            threshold=10
        )

        assert "error" in result
        assert "Magic" in result["error"]


@pytest.mark.asyncio
async def test_skill_check_case_insensitive(mock_db):
    """Test skill_check stat lookup is case-insensitive."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Market",
                stats={"Charisma": 16},
                score=0
            )
        )
        mock_db.get_session.return_value = session

        # Use lowercase stat name
        result = await skill_check.fn(
            session_id="sess1",
            action="Haggle for a better price",
            stat_name="charisma",  # lowercase
            threshold=12
        )

        assert result["success"] is True
        assert result["stat_name"] == "Charisma"  # Returns proper case


@pytest.mark.asyncio
async def test_skill_check_logs_action(mock_db):
    """Test skill_check logs action to history."""
    with patch("adventure_handler.server.db", mock_db):
        from datetime import datetime
        session = GameSession(
            id="sess1",
            adventure_id="adv1",
            created_at=datetime.now(),
            last_played=datetime.now(),
            state=PlayerState(
                session_id="sess1",
                location="Dungeon",
                stats={"Wisdom": 12},
                score=0
            )
        )
        mock_db.get_session.return_value = session

        await skill_check.fn(
            session_id="sess1",
            action="Sense the trap",
            stat_name="Wisdom",
            threshold=10,
            reason="Detecting hidden traps"
        )

        # Verify add_action was called
        mock_db.add_action.assert_called_once()
        call_args = mock_db.add_action.call_args
        assert call_args[0][0] == "sess1"  # session_id
        assert "Sense the trap" in call_args[0][1].action_text
        assert "Success" in call_args[0][2]  # outcome

        # Verify skill check data is stored in dice_roll field
        dice_roll_data = call_args.kwargs.get("dice_roll")
        assert dice_roll_data is not None
        assert dice_roll_data["type"] == "skill_check"
        assert dice_roll_data["stat_value"] == 12
        assert dice_roll_data["threshold"] == 10
        assert dice_roll_data["margin"] == 2
        assert dice_roll_data["success"] is True
        assert dice_roll_data["reason"] == "Detecting hidden traps"
