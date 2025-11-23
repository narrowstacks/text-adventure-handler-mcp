"""SQLite database operations for adventure handler."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import Adventure, GameSession, PlayerState, Action, StatDefinition, WordList, Character, Location, Item, SessionSummary


class AdventureDB:
    """SQLite database for adventure handler."""

    def __init__(self, db_path: str = "adventure_handler.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS adventures (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    prompt TEXT NOT NULL,
                    stats JSON NOT NULL,
                    word_lists JSON DEFAULT '[]',
                    initial_location TEXT NOT NULL,
                    initial_story TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_state (
                    session_id TEXT PRIMARY KEY,
                    score INTEGER DEFAULT 0,
                    location TEXT NOT NULL,
                    stats JSON NOT NULL,
                    inventory JSON NOT NULL,
                    custom_data JSON,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            conn.execute(
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    stats JSON DEFAULT '{}',
                    properties JSON DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id)
                )
                """
            )
            conn.execute(
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
            conn.execute(
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
            conn.execute(
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
            conn.commit()

    def add_adventure(self, adventure: Adventure) -> None:
        """Add a new adventure template."""
        stats_json = json.dumps([s.model_dump() for s in adventure.stats])
        word_lists_json = json.dumps([w.model_dump() for w in adventure.word_lists])
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO adventures
                (id, title, description, prompt, stats, word_lists, initial_location, initial_story)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adventure.id,
                    adventure.title,
                    adventure.description,
                    adventure.prompt,
                    stats_json,
                    word_lists_json,
                    adventure.initial_location,
                    adventure.initial_story,
                ),
            )
            conn.commit()

    def get_adventure(self, adventure_id: str) -> Optional[Adventure]:
        """Retrieve an adventure by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM adventures WHERE id = ?", (adventure_id,)
            ).fetchone()

        if not row:
            return None

        stats = [StatDefinition(**s) for s in json.loads(row["stats"])]
        word_lists_data = json.loads(row["word_lists"]) if "word_lists" in row.keys() else []
        # Handle legacy case where column might be null if added later (though we rebuild DB)
        if word_lists_data is None:
             word_lists_data = []
             
        word_lists = [WordList(**w) for w in word_lists_data]
        
        return Adventure(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            prompt=row["prompt"],
            stats=stats,
            word_lists=word_lists,
            initial_location=row["initial_location"],
            initial_story=row["initial_story"],
        )

    def list_adventures(self) -> list[dict]:
        """List all available adventures."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT id, title, description FROM adventures").fetchall()
        return [dict(row) for row in rows]

    def list_sessions(self, limit: int = 20) -> list[dict]:
        """List recent game sessions with adventure info and last played time."""
        with self._get_conn() as conn:
            rows = conn.execute(
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
            ).fetchall()
        return [dict(row) for row in rows]

    def create_session(self, session_id: str, adventure_id: str) -> bool:
        """Create a new game session."""
        adventure = self.get_adventure(adventure_id)
        if not adventure:
            return False

        now = datetime.now().isoformat()
        stats = {stat.name: stat.default_value for stat in adventure.stats}

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO game_sessions (id, adventure_id, created_at, last_played)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, adventure_id, now, now),
            )
            conn.execute(
                """
                INSERT INTO player_state
                (session_id, location, stats, inventory, custom_data)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    adventure.initial_location,
                    json.dumps(stats),
                    json.dumps([]),
                    json.dumps({}),
                ),
            )
            conn.commit()
        return True

    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Get a game session."""
        with self._get_conn() as conn:
            session_row = conn.execute(
                "SELECT * FROM game_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not session_row:
                return None

            state_row = conn.execute(
                "SELECT * FROM player_state WHERE session_id = ?", (session_id,)
            ).fetchone()

        state = PlayerState(
            session_id=session_id,
            score=state_row["score"],
            location=state_row["location"],
            stats=json.loads(state_row["stats"]),
            inventory=json.loads(state_row["inventory"]),
            custom_data=json.loads(state_row["custom_data"] or "{}"),
        )

        return GameSession(
            id=session_row["id"],
            adventure_id=session_row["adventure_id"],
            created_at=datetime.fromisoformat(session_row["created_at"]),
            last_played=datetime.fromisoformat(session_row["last_played"]),
            state=state,
        )

    def update_player_state(self, session_id: str, state: PlayerState) -> bool:
        """Update player state."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE player_state SET
                score = ?, location = ?, stats = ?, inventory = ?,
                custom_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (
                    state.score,
                    state.location,
                    json.dumps(state.stats),
                    json.dumps(state.inventory),
                    json.dumps(state.custom_data),
                    session_id,
                ),
            )
            conn.commit()
        return True

    def update_last_played(self, session_id: str) -> bool:
        """Update the last_played timestamp for a session."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE game_sessions
                SET last_played = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), session_id),
            )
            conn.commit()
        return True

    def add_action(self, session_id: str, action: Action, outcome: str, score_change: int) -> None:
        """Record a player action."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO action_history
                (session_id, action_text, stat_used, outcome, score_change)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, action.action_text, action.stat_used, outcome, score_change),
            )
            conn.commit()

    def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """Get action history for a session."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT action_text, stat_used, outcome, score_change, timestamp
                FROM action_history WHERE session_id = ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    # Character management
    def add_character(self, character: Character) -> None:
        """Add a dynamically created character to the session."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO characters
                (id, session_id, name, description, location, stats, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    character.id,
                    character.session_id,
                    character.name,
                    character.description,
                    character.location,
                    json.dumps(character.stats),
                    json.dumps(character.properties),
                    character.created_at.isoformat(),
                ),
            )
            conn.commit()

    def get_character(self, character_id: str) -> Optional[Character]:
        """Retrieve a character by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            ).fetchone()

        if not row:
            return None

        return Character(
            id=row["id"],
            session_id=row["session_id"],
            name=row["name"],
            description=row["description"],
            location=row["location"],
            stats=json.loads(row["stats"]),
            properties=json.loads(row["properties"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_characters(self, session_id: str) -> list[Character]:
        """List all characters in a session."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM characters WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()

        return [
            Character(
                id=row["id"],
                session_id=row["session_id"],
                name=row["name"],
                description=row["description"],
                location=row["location"],
                stats=json.loads(row["stats"]),
                properties=json.loads(row["properties"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def update_character(self, character: Character) -> bool:
        """Update an existing character."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE characters SET
                name = ?, description = ?, location = ?, stats = ?, properties = ?
                WHERE id = ?
                """,
                (
                    character.name,
                    character.description,
                    character.location,
                    json.dumps(character.stats),
                    json.dumps(character.properties),
                    character.id,
                ),
            )
            conn.commit()
        return True

    def delete_character(self, character_id: str) -> bool:
        """Delete a character."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()
        return True

    # Location management
    def add_location(self, location: Location) -> None:
        """Add a dynamically created location to the session."""
        with self._get_conn() as conn:
            conn.execute(
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
            conn.commit()

    def get_location(self, location_id: str) -> Optional[Location]:
        """Retrieve a location by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM locations WHERE id = ?", (location_id,)
            ).fetchone()

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

    def list_locations(self, session_id: str) -> list[Location]:
        """List all locations in a session."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM locations WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()

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

    def update_location(self, location: Location) -> bool:
        """Update an existing location."""
        with self._get_conn() as conn:
            conn.execute(
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
            conn.commit()
        return True

    def delete_location(self, location_id: str) -> bool:
        """Delete a location."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
            conn.commit()
        return True

    # Item management
    def add_item(self, item: Item) -> None:
        """Add a dynamically created item to the session."""
        with self._get_conn() as conn:
            conn.execute(
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
            conn.commit()

    def get_item(self, item_id: str) -> Optional[Item]:
        """Retrieve an item by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM items WHERE id = ?", (item_id,)
            ).fetchone()

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

    def list_items(self, session_id: str, location: Optional[str] = None) -> list[Item]:
        """List all items in a session, optionally filtered by location."""
        with self._get_conn() as conn:
            if location is not None:
                rows = conn.execute(
                    "SELECT * FROM items WHERE session_id = ? AND location = ? ORDER BY created_at",
                    (session_id, location),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM items WHERE session_id = ? ORDER BY created_at",
                    (session_id,),
                ).fetchall()

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

    def update_item(self, item: Item) -> bool:
        """Update an existing item."""
        with self._get_conn() as conn:
            conn.execute(
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
            conn.commit()
        return True

    def delete_item(self, item_id: str) -> bool:
        """Delete an item."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()
        return True

    # Session summary management
    def add_session_summary(self, summary: SessionSummary) -> None:
        """Add a session summary."""
        with self._get_conn() as conn:
            conn.execute(
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
            conn.commit()

    def get_session_summaries(self, session_id: str) -> list[SessionSummary]:
        """Get all summaries for a session in chronological order."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM session_summaries WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()

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
