import pytest
from unittest.mock import patch
from adventure_handler.dice import roll_d20, roll_check, stat_check


def test_roll_d20():
    """Test basic d20 rolling."""
    with patch("random.randint", return_value=10):
        assert roll_d20() == 10
        assert roll_d20(modifier=5) == 15
        assert roll_d20(modifier=-2) == 8


def test_roll_check_basic():
    """Test roll_check without advantage/disadvantage."""
    with patch("random.randint", return_value=15):
        # Roll 15 + 2 = 17 vs DC 15 -> Success
        result = roll_check(modifier=2, difficulty_class=15)
        assert result.roll == 15
        assert result.total == 17
        assert result.success is True
        assert "rolled 15" in result.message

        # Roll 15 + 0 = 15 vs DC 16 -> Failure
        result = roll_check(difficulty_class=16)
        assert result.success is False


def test_roll_check_advantage():
    """Test roll_check with advantage."""
    # First call 5, second call 15. Should take 15.
    with patch("random.randint", side_effect=[5, 15]):
        result = roll_check(advantage=True)
        assert result.roll == 15
        assert result.success is True # Default DC 10, 15 >= 10
        assert "(advantage)" in result.message

    # First call 18, second call 2. Should take 18.
    with patch("random.randint", side_effect=[18, 2]):
        result = roll_check(advantage=True)
        assert result.roll == 18


def test_roll_check_disadvantage():
    """Test roll_check with disadvantage."""
    # First call 5, second call 15. Should take 5.
    with patch("random.randint", side_effect=[5, 15]):
        result = roll_check(disadvantage=True)
        assert result.roll == 5
        assert result.success is False # Default DC 10, 5 < 10
        assert "(disadvantage)" in result.message


def test_roll_check_invalid():
    """Test that providing both advantage and disadvantage raises ValueError."""
    with pytest.raises(ValueError, match="Cannot have both"):
        roll_check(advantage=True, disadvantage=True)


def test_stat_check():
    """Test stat_check modifier calculation."""
    # Stat 10 -> Mod 0. Roll 10 -> Total 10.
    with patch("random.randint", return_value=10):
        result = stat_check(stat_value=10)
        assert result.modifier == 0
        assert result.total == 10

    # Stat 12 -> Mod +1. Roll 10 -> Total 11.
    with patch("random.randint", return_value=10):
        result = stat_check(stat_value=12)
        assert result.modifier == 1
        assert result.total == 11

    # Stat 8 -> Mod -1. Roll 10 -> Total 9.
    with patch("random.randint", return_value=10):
        result = stat_check(stat_value=8)
        assert result.modifier == -1
        assert result.total == 9

    # Stat 15 -> Mod +2 (floor(2.5)). Roll 10 -> Total 12.
    with patch("random.randint", return_value=10):
        result = stat_check(stat_value=15)
        assert result.modifier == 2
        assert result.total == 12
