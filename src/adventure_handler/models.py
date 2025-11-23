"""Pydantic models for adventure handler."""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class StatDefinition(BaseModel):
    """Definition of a character stat for an adventure."""
    name: str
    description: str
    default_value: int = 10
    min_value: int = 0
    max_value: int = 20


class WordCategory(BaseModel):
    """A category of words within a word list."""
    name: str
    description: str
    words: list[str]


class WordList(BaseModel):
    """A collection of predefined words for dynamic content generation."""
    name: str
    description: str
    categories: dict[str, list[str]]  # category_name -> [words]


class Adventure(BaseModel):
    """An adventure template."""
    id: str
    title: str
    description: str
    prompt: str  # System prompt for AI to generate story beats
    stats: list[StatDefinition]
    word_lists: list[WordList]  # Predefined words for dynamic generation
    initial_location: str
    initial_story: str


class PlayerState(BaseModel):
    """Current player state in a game session."""
    session_id: str
    score: int = 0
    location: str
    stats: dict[str, int]  # stat_name -> value
    inventory: list[str] = []
    custom_data: dict[str, Any] = {}


class DiceRoll(BaseModel):
    """Result of a dice roll."""
    roll: int = Field(ge=1, le=20)
    modifier: int = 0
    total: int
    dc: Optional[int] = None
    success: Optional[bool] = None
    message: str


class GameSession(BaseModel):
    """Represents an active game session."""
    id: str
    adventure_id: str
    created_at: datetime
    last_played: datetime
    state: PlayerState


class Action(BaseModel):
    """Player action in the game."""
    session_id: str
    action_text: str
    stat_used: Optional[str] = None
    difficulty_class: int = 10
    timestamp: datetime


class ActionResult(BaseModel):
    """Result of a player action."""
    success: bool
    dice_roll: DiceRoll
    outcome: str  # AI-generated story outcome
    score_change: int = 0
    state_changes: dict[str, Any] = {}


class Character(BaseModel):
    """A dynamically created NPC or character in the game world."""
    id: str
    session_id: str
    name: str
    description: str
    location: str  # Where this character is currently located
    stats: dict[str, int] = {}  # Optional stats for interaction
    properties: dict[str, Any] = {}  # Custom properties (hostile, friendly, quest_giver, etc.)
    created_at: datetime = Field(default_factory=datetime.now)


class Location(BaseModel):
    """A dynamically created location in the game world."""
    id: str
    session_id: str
    name: str
    description: str
    connected_to: list[str] = []  # List of location names/IDs that connect to this one
    properties: dict[str, Any] = {}  # Custom properties (locked, hidden, dangerous, etc.)
    created_at: datetime = Field(default_factory=datetime.now)


class Item(BaseModel):
    """A dynamically created item in the game world."""
    id: str
    session_id: str
    name: str
    description: str
    location: Optional[str] = None  # Where the item is located (None if in player inventory)
    properties: dict[str, Any] = {}  # Custom properties (usable, consumable, key_item, etc.)
    created_at: datetime = Field(default_factory=datetime.now)


class SessionSummary(BaseModel):
    """A summary of a game session for story continuity."""
    id: str
    session_id: str
    summary: str  # AI-generated summary of the session
    key_events: list[str] = []  # Important story beats
    character_changes: list[str] = []  # Notable character developments
    created_at: datetime = Field(default_factory=datetime.now)
