from adventure_handler.models import (
    StatDefinition,
    PlayerState,
    DiceRoll,
    GameSession
)
from datetime import datetime
import pytest
from pydantic import ValidationError


def test_stat_definition_defaults():
    """Test StatDefinition defaults."""
    stat = StatDefinition(name="Strength", description="Physical power")
    assert stat.default_value == 10
    assert stat.min_value == 0
    assert stat.max_value == 20


def test_player_state_defaults():
    """Test PlayerState defaults."""
    state = PlayerState(
        session_id="test-session",
        location="Start",
        stats={"Strength": 10}
    )
    assert state.hp == 10
    assert state.max_hp == 10
    assert state.score == 0
    assert state.inventory == []
    assert state.quests == []


def test_dice_roll_validation():
    """Test DiceRoll validation."""
    # Valid roll
    roll = DiceRoll(roll=10, total=10, message="Test")
    assert roll.roll == 10

    # Invalid roll (too low)
    with pytest.raises(ValidationError):
        DiceRoll(roll=0, total=0, message="Fail")

    # Invalid roll (too high)
    with pytest.raises(ValidationError):
        DiceRoll(roll=21, total=21, message="Fail")


def test_game_session_structure():
    """Test GameSession creation."""
    now = datetime.now()
    state = PlayerState(
        session_id="sess1",
        location="loc1",
        stats={}
    )
    session = GameSession(
        id="sess1",
        adventure_id="adv1",
        created_at=now,
        last_played=now,
        state=state
    )
    assert session.id == "sess1"
    assert session.state.session_id == "sess1"
