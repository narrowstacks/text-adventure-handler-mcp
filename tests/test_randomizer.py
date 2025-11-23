import pytest
from unittest.mock import patch
from adventure_handler.randomizer import (
    get_random_word,
    generate_word_prompt,
    process_template,
)
from adventure_handler.models import Adventure, WordList, StatDefinition


@pytest.fixture
def sample_adventure():
    return Adventure(
        id="test-adv",
        title="Test",
        description="Test",
        prompt="Test",
        stats=[StatDefinition(name="Test", description="Test")],
        initial_location="Test",
        initial_story="Test",
        word_lists=[
            WordList(
                name="colors",
                description="List of colors",
                categories={
                    "primary": ["red", "blue", "yellow"],
                    "secondary": ["green", "orange", "purple"],
                },
            ),
            WordList(
                name="weapons",
                description="List of weapons",
                categories={"melee": ["sword", "axe"]},
            ),
        ],
    )


def test_get_random_word_specific_category(sample_adventure):
    """Test getting a random word from a specific category."""
    with patch("random.choice", return_value="red"):
        word = get_random_word(sample_adventure, "colors", "primary")
        assert word == "red"


def test_get_random_word_any_category(sample_adventure):
    """Test getting a random word from any category in the list."""
    # Should flatten all colors
    with patch("random.choice", return_value="green"):
        word = get_random_word(sample_adventure, "colors")
        assert word == "green"


def test_get_random_word_not_found(sample_adventure):
    """Test behaviors when list or category is missing."""
    # Missing list
    assert get_random_word(sample_adventure, "missing_list") is None

    # Missing category
    assert get_random_word(sample_adventure, "colors", "missing_category") is None
    
    # Empty category (if somehow possible via empty list in model)
    # Currently model validation might prevent this but good to handle safely if it happens


def test_generate_word_prompt():
    """Test prompt generation string."""
    prompt = generate_word_prompt("monster", "undead", "graveyard")
    assert "monster" in prompt
    assert "undead" in prompt
    assert "graveyard" in prompt
    assert "Return only the word/name" in prompt


def test_process_template(sample_adventure):
    """Test replacing placeholders in a template."""
    template = "I see a {colors.primary} {weapons.melee}."
    
    # Mock random.choice to return specific values in order
    # 1. colors.primary -> red
    # 2. weapons.melee -> sword
    with patch("random.choice", side_effect=["red", "sword"]):
        result = process_template(template, sample_adventure)
        assert result == "I see a red sword."


def test_process_template_any_category(sample_adventure):
    """Test replacing placeholders without category."""
    template = "I see a {colors}."
    
    with patch("random.choice", side_effect=["green"]):
        result = process_template(template, sample_adventure)
        assert result == "I see a green."


def test_process_template_missing_placeholder(sample_adventure):
    """Test that missing placeholders are left alone."""
    template = "I see a {missing_list}."
    result = process_template(template, sample_adventure)
    assert result == "I see a {missing_list}."
