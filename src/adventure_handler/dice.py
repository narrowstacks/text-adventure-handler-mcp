"""Dice rolling and check logic."""
import random
from .models import DiceRoll


def roll_d20(modifier: int = 0) -> int:
    """Roll a d20 die and add modifier."""
    return random.randint(1, 20) + modifier


def roll_check(
    modifier: int = 0,
    difficulty_class: int = 10,
    advantage: bool = False,
    disadvantage: bool = False,
) -> DiceRoll:
    """
    Perform a d20 check against a difficulty class.

    Args:
        modifier: Bonus/penalty to add to roll
        difficulty_class: Target number to meet or exceed
        advantage: Roll twice, take higher result
        disadvantage: Roll twice, take lower result
    """
    if advantage and disadvantage:
        raise ValueError("Cannot have both advantage and disadvantage")

    if advantage:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        roll = max(roll1, roll2)
    elif disadvantage:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        roll = min(roll1, roll2)
    else:
        roll = random.randint(1, 20)

    total = roll + modifier
    success = total >= difficulty_class

    message = f"d20{modifier:+d} vs DC{difficulty_class}: rolled {roll}, total {total}"
    if advantage:
        message += " (advantage)"
    elif disadvantage:
        message += " (disadvantage)"

    return DiceRoll(
        roll=roll,
        modifier=modifier,
        total=total,
        dc=difficulty_class,
        success=success,
        message=message,
    )


def stat_check(
    stat_value: int,
    difficulty_class: int = 10,
    advantage: bool = False,
    disadvantage: bool = False,
) -> DiceRoll:
    """
    Roll with stat bonus (stat_value - 10) / 2 rounded down.
    Uses standard D&D stat modifier calculation.
    """
    modifier = (stat_value - 10) // 2
    return roll_check(
        modifier=modifier,
        difficulty_class=difficulty_class,
        advantage=advantage,
        disadvantage=disadvantage,
    )
