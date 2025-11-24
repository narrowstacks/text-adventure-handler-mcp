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


class InventoryItem(BaseModel):
    """An item in the player's inventory with rich properties."""
    id: str
    name: str
    description: str
    quantity: int = 1
    properties: dict[str, Any] = {} # e.g. {"damage": 5, "heal": 10, "equippable": True}


class QuestStatus(BaseModel):
    """Tracking for a quest."""
    id: str
    title: str
    description: str
    status: str = "active" # active, completed, failed
    objectives: list[str]
    completed_objectives: list[str] = []
    rewards: dict[str, Any] = {}


class PlayerState(BaseModel):
    """Current player state in a game session."""
    session_id: str
    hp: int = 10
    max_hp: int = 10
    score: int = 0
    location: str
    stats: dict[str, int]  # stat_name -> value
    inventory: list[InventoryItem] = []
    quests: list[QuestStatus] = []
    relationships: dict[str, int] = {} # npc_name -> value (-100 to 100)
    custom_data: dict[str, Any] = {}
    currency: int = 0  # Money/gold/credits
    game_time: int = 0  # Current time in hours (0-23)
    game_day: int = 1  # Current day number


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


class FeatureConfig(BaseModel):
    """Configuration for which game features are enabled."""
    status_effects: bool = False
    time_tracking: bool = False
    factions: bool = False
    currency: bool = False


class TimeConfig(BaseModel):
    """Configuration for time tracking."""
    starting_hour: int = 8
    starting_day: int = 1


class CurrencyConfig(BaseModel):
    """Configuration for currency system."""
    name: str = "gold"
    starting_amount: int = 0


class FactionDefinition(BaseModel):
    """Predefined faction for an adventure."""
    id: str
    name: str
    description: str
    initial_reputation: int = 0


class Adventure(BaseModel):
    """An adventure template."""
    id: str
    title: str
    description: str
    prompt: str  # System prompt for AI to generate story beats
    stats: list[StatDefinition]
    starting_hp: int = 10
    word_lists: list[WordList]  # Predefined words for dynamic generation
    initial_location: str
    initial_story: str
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    time_config: TimeConfig = Field(default_factory=TimeConfig)
    currency_config: CurrencyConfig = Field(default_factory=CurrencyConfig)
    factions: list[FactionDefinition] = []


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


class Memory(BaseModel):
    """A memory held by a character."""
    id: str
    description: str
    timestamp: datetime
    type: str = "observation"  # observation, interaction, rumor
    importance: int = 1  # 1-10, determines retention and influence
    tags: list[str] = []
    related_entities: list[str] = []  # IDs of related characters/items


class Character(BaseModel):
    """A dynamically created NPC or character in the game world."""
    id: str
    session_id: str
    name: str
    description: str
    location: str  # Where this character is currently located
    stats: dict[str, int] = {}  # Optional stats for interaction
    properties: dict[str, Any] = {}  # Custom properties (hostile, friendly, quest_giver, etc.)
    memories: list[Memory] = []
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


class NarratorThought(BaseModel):
    """Internal thought process of the AI narrator."""
    id: str
    session_id: str
    thought: str
    story_status: str # on_track, off_rails, user_deviating, completed, stalled
    plan: str
    user_behavior: str # cooperative, creative, disruptive, cheating
    created_at: datetime = Field(default_factory=datetime.now)


class StatusEffect(BaseModel):
    """A temporary or permanent status effect on the player."""
    id: str
    session_id: str
    name: str
    description: str
    duration: int  # -1 for permanent, 0 for expired, >0 for remaining turns/actions
    stat_modifiers: dict[str, int] = {}  # stat_name -> modifier (can be negative)
    properties: dict[str, Any] = {}  # Custom properties (stackable, harmful, beneficial, etc.)
    created_at: datetime = Field(default_factory=datetime.now)


class Faction(BaseModel):
    """A faction with reputation tracking."""
    id: str
    session_id: str
    name: str
    description: str
    reputation: int = 0  # -100 (hostile) to +100 (revered)
    properties: dict[str, Any] = {}  # Custom properties (main_quest, hidden, etc.)
    created_at: datetime = Field(default_factory=datetime.now)
