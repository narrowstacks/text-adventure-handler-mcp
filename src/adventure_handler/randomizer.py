"""Word randomizer utility for dynamic content generation."""
import random
import re
from .models import Adventure


def get_random_word(
    adventure: Adventure,
    word_list_name: str,
    category_name: str | None = None,
) -> str | None:
    """
    Get a random word from an adventure's predefined word list.

    Args:
        adventure: The adventure template
        word_list_name: Name of the word list to draw from
        category_name: Optional category within the word list

    Returns:
        A random word from the list, or None if not found
    """
    word_list = next(
        (wl for wl in adventure.word_lists if wl.name == word_list_name),
        None,
    )

    if not word_list:
        return None

    if category_name:
        words = word_list.categories.get(category_name, [])
    else:
        # Flatten all categories if no specific category requested
        words = []
        for category_words in word_list.categories.values():
            words.extend(category_words)

    if not words:
        return None

    return random.choice(words)


def generate_word_prompt(
    word_list_name: str,
    category_name: str | None = None,
    context: str | None = None,
) -> str:
    """
    Generate a prompt for the AI to create a new word dynamically.

    Args:
        word_list_name: Name of the word list type to generate
        category_name: Optional category for more specific generation
        context: Optional context for the generation (e.g., adventure theme)

    Returns:
        A prompt string for the AI to use
    """
    category_part = f" in the {category_name} category" if category_name else ""
    context_part = f" for a {context}" if context else ""

    return (
        f"Generate a unique {word_list_name.replace('_', ' ')}{category_part}"
        f"{context_part}. Return only the word/name, no explanation."
    )


def process_template(template: str, adventure: Adventure) -> str:
    """
    Process a template string and substitute word list placeholders with random words.

    Syntax:
    - {word_list_name} - pick from any category in the word list
    - {word_list_name.category_name} - pick from specific category

    Args:
        template: Template string with placeholders
        adventure: The adventure containing word lists

    Returns:
        Processed string with placeholders replaced by random words
    """

    def replace_placeholder(match: re.Match) -> str:
        placeholder = match.group(1)

        # Parse placeholder: "word_list_name" or "word_list_name.category_name"
        if "." in placeholder:
            word_list_name, category_name = placeholder.split(".", 1)
        else:
            word_list_name = placeholder
            category_name = None

        # Get random word
        word = get_random_word(adventure, word_list_name, category_name)
        return word if word else match.group(0)  # Return original if not found

    # Replace all {word_list} and {word_list.category} placeholders
    return re.sub(r"\{([a-zA-Z0-9_.]+)\}", replace_placeholder, template)
