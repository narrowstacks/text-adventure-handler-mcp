import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from adventure_handler.models import Character, GameSession, PlayerState
from adventure_handler.server import manage_character
from datetime import datetime

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_session():
    return GameSession(
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

@pytest.mark.asyncio
async def test_manage_character_create_success(mock_db, mock_session):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.get_session.return_value = mock_session
        
        char_data = {
            "name": "Test Char",
            "description": "A test character",
            "location": "Start"
        }
        
        result = await manage_character.fn(
            session_id="sess1",
            action="create",
            character_data=char_data
        )
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert "character_id" in result
        mock_db.add_character.assert_called_once()

@pytest.mark.asyncio
async def test_manage_character_create_missing_fields(mock_db, mock_session):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.get_session.return_value = mock_session
        
        # Missing 'location'
        char_data = {
            "name": "Test Char",
            "description": "A test character"
        }
        
        result = await manage_character.fn(
            session_id="sess1",
            action="create",
            character_data=char_data
        )
        
        assert "error" in result
        assert "Missing required fields" in result["error"]
        assert "location" in result["error"]
        mock_db.add_character.assert_not_called()

@pytest.mark.asyncio
async def test_manage_character_read(mock_db, mock_session):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.get_session.return_value = mock_session
        
        char = Character(
            id="char1",
            session_id="sess1",
            name="Test Char",
            description="Desc",
            location="Loc",
            stats={},
            properties={},
            memories=[]
        )
        mock_db.get_character.return_value = char
        
        result = await manage_character.fn(
            session_id="sess1",
            action="read",
            character_id="char1"
        )
        
        assert result["success"] is True
        assert result["data"]["id"] == "char1"

@pytest.mark.asyncio
async def test_manage_character_update(mock_db, mock_session):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.get_session.return_value = mock_session
        
        char = Character(
            id="char1",
            session_id="sess1",
            name="Old Name",
            description="Desc",
            location="Loc",
            stats={},
            properties={},
            memories=[]
        )
        mock_db.get_character.return_value = char
        
        result = await manage_character.fn(
            session_id="sess1",
            action="update",
            character_id="char1",
            character_data={"name": "New Name"}
        )
        
        assert result["success"] is True
        assert char.name == "New Name"
        mock_db.update_character.assert_called_once()

@pytest.mark.asyncio
async def test_manage_character_delete(mock_db, mock_session):
    with patch("adventure_handler.server.db", mock_db):
        mock_db.get_session.return_value = mock_session
        
        result = await manage_character.fn(
            session_id="sess1",
            action="delete",
            character_id="char1"
        )
        
        assert result["success"] is True
        mock_db.delete_character.assert_called_once_with("char1")
