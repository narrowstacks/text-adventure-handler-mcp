"""SQLite database operations for adventure handler."""
import json
import aiosqlite
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import (
    Adventure, GameSession, PlayerState, Action, StatDefinition, WordList,
    Character, Location, Item, SessionSummary, InventoryItem, QuestStatus,
    NarratorThought, Memory, StatusEffect, Faction, FeatureConfig, TimeConfig,
    CurrencyConfig, FactionDefinition
)


class AdventureDB:
    """SQLite database for adventure handler."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Check environment variable first
            env_path = os.environ.get("ADVENTURE_DB_PATH")
            if env_path:
                db_path = env_path
            else:
                # Default to user's home directory for persistence across uvx runs
                db_path = Path.home() / ".text-adventure-handler" / "adventure_handler.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_conn(self) -> aiosqlite.Connection:
        """Get database connection with row factory."""
        conn = aiosqlite.connect(str(self.db_path))
        return conn

    async def init_db(self):
        """Initialize database schema."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS adventures (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    prompt TEXT NOT NULL,
                    stats JSON NOT NULL,
                    starting_hp INTEGER DEFAULT 10,
                    word_lists JSON DEFAULT '[]',
                    initial_location TEXT NOT NULL,
                    initial_story TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS narrator_thoughts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    thought TEXT NOT NULL,
                    story_status TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    user_behavior TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id TEXT PRIMARY KEY,
                    adventure_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_played TEXT NOT NULL,
                    FOREIGN KEY (adventure_id) REFERENCES adventures(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_state (
                    session_id TEXT PRIMARY KEY,
                    hp INTEGER DEFAULT 10,
                    max_hp INTEGER DEFAULT 10,
                    score INTEGER DEFAULT 0,
                    location TEXT NOT NULL,
                    stats JSON NOT NULL,
                    inventory JSON NOT NULL,
                    quests JSON DEFAULT '[]',
                    relationships JSON DEFAULT '{}',
                    custom_data JSON,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS action_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    action_text TEXT NOT NULL,
                    stat_used TEXT,
                    dice_roll JSON NOT NULL,
                    outcome TEXT,
                    score_change INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    stats JSON DEFAULT '{}',
                    properties JSON DEFAULT '{}',
                    memories JSON DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            
            # Migration for existing databases (idempotent-ish)
            try:
                await conn.execute("ALTER TABLE characters ADD COLUMN memories JSON DEFAULT '[]'")
            except Exception:
                pass # Column likely exists

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS locations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    connected_to JSON DEFAULT '[]',
                    properties JSON DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT,
                    properties JSON DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    key_events JSON DEFAULT '[]',
                    character_changes JSON DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS status_effects (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    stat_modifiers JSON DEFAULT '{}',
                    properties JSON DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    reputation INTEGER DEFAULT 0,
                    properties JSON DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )

            # Migration for existing databases to add new fields to player_state
            try:
                await conn.execute("ALTER TABLE player_state ADD COLUMN currency INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE player_state ADD COLUMN game_time INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE player_state ADD COLUMN game_day INTEGER DEFAULT 1")
            except Exception:
                pass

            # Migration for adventures table to add starting_hp (older databases)
            try:
                await conn.execute("ALTER TABLE adventures ADD COLUMN starting_hp INTEGER DEFAULT 10")
            except Exception:
                pass

            # Migration for adventures table to add new feature configs
            try:
                await conn.execute("ALTER TABLE adventures ADD COLUMN features JSON DEFAULT '{}'")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE adventures ADD COLUMN time_config JSON DEFAULT '{}'")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE adventures ADD COLUMN currency_config JSON DEFAULT '{}'")
            except Exception:
                pass
            try:
                await conn.execute("ALTER TABLE adventures ADD COLUMN factions JSON DEFAULT '[]'")
            except Exception:
                pass

            await conn.commit()

    async def add_adventure(self, adventure: Adventure) -> None:
        """Add a new adventure template."""
        stats_json = json.dumps([s.model_dump() for s in adventure.stats])
        word_lists_json = json.dumps([w.model_dump() for w in adventure.word_lists])
        features_json = json.dumps(adventure.features.model_dump())
        time_config_json = json.dumps(adventure.time_config.model_dump())
        currency_config_json = json.dumps(adventure.currency_config.model_dump())
        factions_json = json.dumps([f.model_dump() for f in adventure.factions])

        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO adventures
                (id, title, description, prompt, stats, starting_hp, word_lists, initial_location, initial_story,
                 features, time_config, currency_config, factions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adventure.id,
                    adventure.title,
                    adventure.description,
                    adventure.prompt,
                    stats_json,
                    adventure.starting_hp,
                    word_lists_json,
                    adventure.initial_location,
                    adventure.initial_story,
                    features_json,
                    time_config_json,
                    currency_config_json,
                    factions_json,
                ),
            )
            await conn.commit()

    async def get_adventure(self, adventure_id: str) -> Optional[Adventure]:
        """Retrieve an adventure by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM adventures WHERE id = ?", (adventure_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        stats = [StatDefinition(**s) for s in json.loads(row["stats"])]
        word_lists_data = json.loads(row["word_lists"]) if "word_lists" in row.keys() else []
        if word_lists_data is None:
             word_lists_data = []

        word_lists = [WordList(**w) for w in word_lists_data]

        # Load new feature configs with defaults for backward compatibility
        features_data = json.loads(row["features"]) if "features" in row.keys() and row["features"] else {}
        features = FeatureConfig(**features_data) if features_data else FeatureConfig()

        time_config_data = json.loads(row["time_config"]) if "time_config" in row.keys() and row["time_config"] else {}
        time_config = TimeConfig(**time_config_data) if time_config_data else TimeConfig()

        currency_config_data = json.loads(row["currency_config"]) if "currency_config" in row.keys() and row["currency_config"] else {}
        currency_config = CurrencyConfig(**currency_config_data) if currency_config_data else CurrencyConfig()

        factions_data = json.loads(row["factions"]) if "factions" in row.keys() and row["factions"] else []
        factions = [FactionDefinition(**f) for f in factions_data]

        return Adventure(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            prompt=row["prompt"],
            stats=stats,
            starting_hp=row["starting_hp"] if "starting_hp" in row.keys() and row["starting_hp"] is not None else 10,
            word_lists=word_lists,
            initial_location=row["initial_location"],
            initial_story=row["initial_story"],
            features=features,
            time_config=time_config,
            currency_config=currency_config,
            factions=factions,
        )

    async def list_adventures(self) -> list[dict]:
        """List all available adventures."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT id, title, description FROM adventures") as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def list_sessions(self, limit: int = 20) -> list[dict]:
        """List recent game sessions with adventure info and last played time."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """
                SELECT
                    gs.id,
                    gs.adventure_id,
                    a.title as adventure_title,
                    gs.created_at,
                    gs.last_played,
                    ps.location,
                    ps.score
                FROM game_sessions gs
                JOIN adventures a ON gs.adventure_id = a.id
                JOIN player_state ps ON gs.id = ps.session_id
                ORDER BY gs.last_played DESC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def create_session(self, session_id: str, adventure_id: str) -> bool:
        """Create a new game session."""
        adventure = await self.get_adventure(adventure_id)
        if not adventure:
            return False

        now = datetime.now().isoformat()
        stats = {stat.name: stat.default_value for stat in adventure.stats}

        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO game_sessions (id, adventure_id, created_at, last_played)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, adventure_id, now, now),
            )
            await conn.execute(
                """
                INSERT INTO player_state
                (session_id, hp, max_hp, location, stats, inventory, quests, relationships, custom_data,
                 currency, game_time, game_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    adventure.starting_hp,
                    adventure.starting_hp,
                    adventure.initial_location,
                    json.dumps(stats),
                    json.dumps([]),
                    json.dumps([]),
                    json.dumps({}),
                    json.dumps({}),
                    adventure.currency_config.starting_amount,
                    adventure.time_config.starting_hour,
                    adventure.time_config.starting_day,
                ),
            )
            await conn.commit()

            # Initialize factions if defined in adventure
            for faction_def in adventure.factions:
                faction = Faction(
                    id=f"{session_id}_{faction_def.id}",
                    session_id=session_id,
                    name=faction_def.name,
                    description=faction_def.description,
                    reputation=faction_def.initial_reputation,
                )
                await self.add_faction(faction)

        return True

    async def get_session(self, session_id: str) -> Optional[GameSession]:
        """Get a game session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM game_sessions WHERE id = ?", (session_id,)
            ) as cursor:
                session_row = await cursor.fetchone()
            
            if not session_row:
                return None

            async with conn.execute(
                "SELECT * FROM player_state WHERE session_id = ?", (session_id,)
            ) as cursor:
                state_row = await cursor.fetchone()

        # Safe loading of JSON fields with defaults
        inventory_data = json.loads(state_row["inventory"])
        inventory = [InventoryItem(**i) for i in inventory_data]

        quests_data = json.loads(state_row["quests"]) if "quests" in state_row.keys() and state_row["quests"] else []
        quests = [QuestStatus(**q) for q in quests_data]

        relationships = json.loads(state_row["relationships"]) if "relationships" in state_row.keys() and state_row["relationships"] else {}
        hp = state_row["hp"] if "hp" in state_row.keys() and state_row["hp"] is not None else 10
        max_hp = state_row["max_hp"] if "max_hp" in state_row.keys() and state_row["max_hp"] is not None else 10
        currency = state_row["currency"] if "currency" in state_row.keys() and state_row["currency"] is not None else 0
        game_time = state_row["game_time"] if "game_time" in state_row.keys() and state_row["game_time"] is not None else 0
        game_day = state_row["game_day"] if "game_day" in state_row.keys() and state_row["game_day"] is not None else 1

        state = PlayerState(
            session_id=session_id,
            hp=hp,
            max_hp=max_hp,
            score=state_row["score"],
            location=state_row["location"],
            stats=json.loads(state_row["stats"]),
            inventory=inventory,
            quests=quests,
            relationships=relationships,
            custom_data=json.loads(state_row["custom_data"] or "{}"),
            currency=currency,
            game_time=game_time,
            game_day=game_day,
        )

        return GameSession(
            id=session_row["id"],
            adventure_id=session_row["adventure_id"],
            created_at=datetime.fromisoformat(session_row["created_at"]),
            last_played=datetime.fromisoformat(session_row["last_played"]),
            state=state,
        )

    async def update_player_state(self, session_id: str, state: PlayerState) -> bool:
        """Update player state."""
        inventory_json = json.dumps([i.model_dump() for i in state.inventory])
        quests_json = json.dumps([q.model_dump() for q in state.quests])

        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE player_state SET
                hp = ?, max_hp = ?, score = ?, location = ?, stats = ?, inventory = ?,
                quests = ?, relationships = ?, custom_data = ?, currency = ?, game_time = ?, game_day = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (
                    state.hp,
                    state.max_hp,
                    state.score,
                    state.location,
                    json.dumps(state.stats),
                    inventory_json,
                    quests_json,
                    json.dumps(state.relationships),
                    json.dumps(state.custom_data),
                    state.currency,
                    state.game_time,
                    state.game_day,
                    session_id,
                ),
            )
            await conn.commit()
        return True

    async def update_last_played(self, session_id: str) -> bool:
        """Update the last_played timestamp for a session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE game_sessions
                SET last_played = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), session_id),
            )
            await conn.commit()
        return True

    async def add_action(self, session_id: str, action: Action, outcome: str, score_change: int, dice_roll: Optional[dict] = None) -> None:
        """Record a player action."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO action_history
                (session_id, action_text, stat_used, dice_roll, outcome, score_change)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, 
                    action.action_text, 
                    action.stat_used, 
                    json.dumps(dice_roll) if dice_roll else "{}", 
                    outcome, 
                    score_change
                ),
            )
            await conn.commit()

    async def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """Get action history for a session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """
                SELECT action_text, stat_used, outcome, score_change, timestamp
                FROM action_history WHERE session_id = ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (session_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]

    # Character management
    async def add_character(self, character: Character) -> None:
        """Add a dynamically created character to the session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO characters
                (id, session_id, name, description, location, stats, properties, memories, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    character.id,
                    character.session_id,
                    character.name,
                    character.description,
                    character.location,
                    json.dumps(character.stats),
                    json.dumps(character.properties),
                    json.dumps([m.model_dump(mode='json') for m in character.memories]),
                    character.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_character(self, character_id: str) -> Optional[Character]:
        """Retrieve a character by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        memories_data = json.loads(row["memories"]) if "memories" in row.keys() and row["memories"] else []
        memories = [Memory(**m) for m in memories_data]

        return Character(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            location=row["location"],
            stats=json.loads(row["stats"]),
            properties=json.loads(row["properties"]),
            memories=memories,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def list_characters(self, session_id: str) -> list[Character]:
        """List all characters in a session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM characters WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

        characters = []
        for row in rows:
            memories_data = json.loads(row["memories"]) if "memories" in row.keys() and row["memories"] else []
            memories = [Memory(**m) for m in memories_data]
            
            characters.append(Character(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                location=row["location"],
                stats=json.loads(row["stats"]),
                properties=json.loads(row["properties"]),
                memories=memories,
                created_at=datetime.fromisoformat(row["created_at"]),
            ))
        return characters

    async def update_character(self, character: Character) -> bool:
        """Update an existing character."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE characters SET
                name = ?, description = ?, location = ?, stats = ?, properties = ?, memories = ?
                WHERE id = ?
                """,
                (
                    character.name,
                    character.description,
                    character.location,
                    json.dumps(character.stats),
                    json.dumps(character.properties),
                    json.dumps([m.model_dump(mode='json') for m in character.memories]),
                    character.id,
                ),
            )
            await conn.commit()
        return True

    async def delete_character(self, character_id: str) -> bool:
        """Delete a character."""
        async with self._get_conn() as conn:
            await conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            await conn.commit()
        return True

    # Location management
    async def add_location(self, location: Location) -> None:
        """Add a dynamically created location to the session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO locations
                (id, session_id, name, description, connected_to, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location.id,
                    location.session_id,
                    location.name,
                    location.description,
                    json.dumps(location.connected_to),
                    json.dumps(location.properties),
                    location.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_location(self, location_id: str) -> Optional[Location]:
        """Retrieve a location by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM locations WHERE id = ?", (location_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        return Location(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            connected_to=json.loads(row["connected_to"]),
            properties=json.loads(row["properties"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def list_locations(self, session_id: str) -> list[Location]:
        """List all locations in a session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM locations WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            Location(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                connected_to=json.loads(row["connected_to"]),
                properties=json.loads(row["properties"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def update_location(self, location: Location) -> bool:
        """Update an existing location."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE locations SET
                name = ?, description = ?, connected_to = ?, properties = ?
                WHERE id = ?
                """,
                (
                    location.name,
                    location.description,
                    json.dumps(location.connected_to),
                    json.dumps(location.properties),
                    location.id,
                ),
            )
            await conn.commit()
        return True

    async def delete_location(self, location_id: str) -> bool:
        """Delete a location."""
        async with self._get_conn() as conn:
            await conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
            await conn.commit()
        return True

    # Item management
    async def add_item(self, item: Item) -> None:
        """Add a dynamically created item to the session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO items
                (id, session_id, name, description, location, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.session_id,
                    item.name,
                    item.description,
                    item.location,
                    json.dumps(item.properties),
                    item.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_item(self, item_id: str) -> Optional[Item]:
        """Retrieve an item by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM items WHERE id = ?", (item_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        return Item(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            location=row["location"],
            properties=json.loads(row["properties"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def list_items(self, session_id: str, location: Optional[str] = None) -> list[Item]:
        """List all items in a session, optionally filtered by location."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            if location is not None:
                async with conn.execute(
                    "SELECT * FROM items WHERE session_id = ? AND location = ? ORDER BY created_at",
                    (session_id, location),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with conn.execute(
                    "SELECT * FROM items WHERE session_id = ? ORDER BY created_at",
                    (session_id,),
                ) as cursor:
                    rows = await cursor.fetchall()

        return [
            Item(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                location=row["location"],
                properties=json.loads(row["properties"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def update_item(self, item: Item) -> bool:
        """Update an existing item."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE items SET
                name = ?, description = ?, location = ?, properties = ?
                WHERE id = ?
                """,
                (
                    item.name,
                    item.description,
                    item.location,
                    json.dumps(item.properties),
                    item.id,
                ),
            )
            await conn.commit()
        return True

    async def delete_item(self, item_id: str) -> bool:
        """Delete an item."""
        async with self._get_conn() as conn:
            await conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            await conn.commit()
        return True

    # Session summary management
    async def add_session_summary(self, summary: SessionSummary) -> None:
        """Add a session summary."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO session_summaries
                (id, session_id, summary, key_events, character_changes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.id,
                    summary.session_id,
                    summary.summary,
                    json.dumps(summary.key_events),
                    json.dumps(summary.character_changes),
                    summary.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def log_thought(self, thought: NarratorThought) -> None:
        """Log an internal thought from the narrator."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT INTO narrator_thoughts
                (id, session_id, thought, story_status, plan, user_behavior, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thought.id,
                    thought.session_id,
                    thought.thought,
                    thought.story_status,
                    thought.plan,
                    thought.user_behavior,
                    thought.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_session_summaries(self, session_id: str) -> list[SessionSummary]:
        """Get all summaries for a session in chronological order."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM session_summaries WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            SessionSummary(
                id=row["id"],
                session_id=row["session_id"],
                summary=row["summary"],
                key_events=json.loads(row["key_events"]),
                character_changes=json.loads(row["character_changes"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    # Status effect management
    async def add_status_effect(self, effect: StatusEffect) -> None:
        """Add a status effect to the session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO status_effects
                (id, session_id, name, description, duration, stat_modifiers, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    effect.id,
                    effect.session_id,
                    effect.name,
                    effect.description,
                    effect.duration,
                    json.dumps(effect.stat_modifiers),
                    json.dumps(effect.properties),
                    effect.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_status_effect(self, effect_id: str) -> Optional[StatusEffect]:
        """Retrieve a status effect by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM status_effects WHERE id = ?", (effect_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        return StatusEffect(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            duration=row["duration"],
            stat_modifiers=json.loads(row["stat_modifiers"]),
            properties=json.loads(row["properties"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def list_status_effects(self, session_id: str, active_only: bool = True) -> list[StatusEffect]:
        """List status effects for a session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            if active_only:
                async with conn.execute(
                    "SELECT * FROM status_effects WHERE session_id = ? AND duration != 0 ORDER BY created_at",
                    (session_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with conn.execute(
                    "SELECT * FROM status_effects WHERE session_id = ? ORDER BY created_at",
                    (session_id,),
                ) as cursor:
                    rows = await cursor.fetchall()

        return [
            StatusEffect(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                duration=row["duration"],
                stat_modifiers=json.loads(row["stat_modifiers"]),
                properties=json.loads(row["properties"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def update_status_effect(self, effect: StatusEffect) -> bool:
        """Update an existing status effect."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE status_effects SET
                name = ?, description = ?, duration = ?, stat_modifiers = ?, properties = ?
                WHERE id = ?
                """,
                (
                    effect.name,
                    effect.description,
                    effect.duration,
                    json.dumps(effect.stat_modifiers),
                    json.dumps(effect.properties),
                    effect.id,
                ),
            )
            await conn.commit()
        return True

    async def delete_status_effect(self, effect_id: str) -> bool:
        """Delete a status effect."""
        async with self._get_conn() as conn:
            await conn.execute("DELETE FROM status_effects WHERE id = ?", (effect_id,))
            await conn.commit()
        return True

    # Faction management
    async def add_faction(self, faction: Faction) -> None:
        """Add a faction to the session."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO factions
                (id, session_id, name, description, reputation, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    faction.id,
                    faction.session_id,
                    faction.name,
                    faction.description,
                    faction.reputation,
                    json.dumps(faction.properties),
                    faction.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_faction(self, faction_id: str) -> Optional[Faction]:
        """Retrieve a faction by ID."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM factions WHERE id = ?", (faction_id,)
            ) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        return Faction(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            reputation=row["reputation"],
            properties=json.loads(row["properties"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def list_factions(self, session_id: str) -> list[Faction]:
        """List all factions in a session."""
        async with self._get_conn() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM factions WHERE session_id = ? ORDER BY name",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

        return [
            Faction(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                reputation=row["reputation"],
                properties=json.loads(row["properties"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def update_faction(self, faction: Faction) -> bool:
        """Update an existing faction."""
        async with self._get_conn() as conn:
            await conn.execute(
                """
                UPDATE factions SET
                name = ?, description = ?, reputation = ?, properties = ?
                WHERE id = ?
                """,
                (
                    faction.name,
                    faction.description,
                    faction.reputation,
                    json.dumps(faction.properties),
                    faction.id,
                ),
            )
            await conn.commit()
        return True

    async def delete_faction(self, faction_id: str) -> bool:
        """Delete a faction."""
        async with self._get_conn() as conn:
            await conn.execute("DELETE FROM factions WHERE id = ?", (faction_id,))
            await conn.commit()
        return True