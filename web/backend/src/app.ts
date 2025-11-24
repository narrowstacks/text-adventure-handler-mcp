import express from 'express';
import cors from 'cors';
import db, { DB_PATH } from './db';

const app = express();
app.use(cors());
app.use(express.json());

/** Utility helpers */
const safeJson = <T>(value: any, fallback: T): T => {
  if (value === null || value === undefined) return fallback;
  try {
    return JSON.parse(value);
  } catch (_) {
    return fallback;
  }
};

const hydrateAdventure = (row: any) => {
  if (!row) return null;
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    prompt: row.prompt,
    stats: safeJson(row.stats, []),
    starting_hp: row.starting_hp ?? 10,
    word_lists: safeJson(row.word_lists, []),
    initial_location: row.initial_location,
    initial_story: row.initial_story,
    features: safeJson(row.features, {}),
    time_config: safeJson(row.time_config, {}),
    currency_config: safeJson(row.currency_config, {}),
    factions: safeJson(row.factions, []),
    created_at: row.created_at,
  };
};

const hydrateState = (row: any) => {
  if (!row) return null;
  return {
    session_id: row.session_id,
    hp: row.hp ?? 10,
    max_hp: row.max_hp ?? 10,
    score: row.score ?? 0,
    location: row.location,
    stats: safeJson(row.stats, {}),
    inventory: safeJson(row.inventory, []),
    quests: safeJson(row.quests, []),
    relationships: safeJson(row.relationships, {}),
    custom_data: safeJson(row.custom_data, {}),
    currency: row.currency ?? 0,
    game_time: row.game_time ?? 0,
    game_day: row.game_day ?? 1,
    updated_at: row.updated_at,
  };
};

const hydrateHistory = (row: any) => ({
  ...row,
  dice_roll: safeJson(row.dice_roll, {}),
});

const loadWorld = (sessionId: string) => {
  const characters = db.query('SELECT * FROM characters WHERE session_id = ? ORDER BY created_at').all(sessionId)
    .map((c: any) => ({
      ...c,
      stats: safeJson(c.stats, {}),
      properties: safeJson(c.properties, {}),
      memories: safeJson(c.memories, []),
    }));

  const locations = db.query('SELECT * FROM locations WHERE session_id = ? ORDER BY created_at').all(sessionId)
    .map((l: any) => ({
      ...l,
      connected_to: safeJson(l.connected_to, []),
      properties: safeJson(l.properties, {}),
    }));

  const items = db.query('SELECT * FROM items WHERE session_id = ? ORDER BY created_at').all(sessionId)
    .map((i: any) => ({
      ...i,
      properties: safeJson(i.properties, {}),
    }));

  const statusEffects = db.query('SELECT * FROM status_effects WHERE session_id = ? ORDER BY created_at').all(sessionId)
    .map((s: any) => ({
      ...s,
      stat_modifiers: safeJson(s.stat_modifiers, {}),
      properties: safeJson(s.properties, {}),
    }));

  const factions = db.query('SELECT * FROM factions WHERE session_id = ? ORDER BY created_at').all(sessionId)
    .map((f: any) => ({
      ...f,
      properties: safeJson(f.properties, {}),
    }));

  return { characters, locations, items, status_effects: statusEffects, factions };
};

/** Routes */
app.get('/api/health', (req, res) => {
  try {
    const sessions = db.query('SELECT COUNT(*) as c FROM game_sessions').get() as { c?: number } | undefined;
    const adventures = db.query('SELECT COUNT(*) as c FROM adventures').get() as { c?: number } | undefined;
    res.json({ status: 'ok', db_path: DB_PATH, sessions: sessions?.c ?? 0, adventures: adventures?.c ?? 0 });
  } catch (error: any) {
    res.status(500).json({ status: 'error', message: error.message });
  }
});

app.get('/api/dashboard', (req, res) => {
  try {
    const totals = db.query('SELECT COUNT(*) as sessions FROM game_sessions').get() as { sessions?: number } | undefined;
    const adventureTotals = db.query('SELECT COUNT(*) as adventures FROM adventures').get() as { adventures?: number } | undefined;
    const active = db.query("SELECT COUNT(*) as active FROM game_sessions WHERE datetime(last_played) >= datetime('now','-2 day')").get() as { active?: number } | undefined;
    const topAdventure = db.query(`
      SELECT a.title as title, COUNT(*) as plays
      FROM game_sessions gs
      JOIN adventures a ON gs.adventure_id = a.id
      GROUP BY gs.adventure_id
      ORDER BY plays DESC
      LIMIT 1
    `).get() as { title: string; plays: number } | undefined;
    const latestActions = db.query('SELECT session_id, action_text, timestamp FROM action_history ORDER BY timestamp DESC LIMIT 6').all() as any[];

    res.json({
      totals: { sessions: totals?.sessions ?? 0, adventures: adventureTotals?.adventures ?? 0 },
      active_sessions: active?.active ?? 0,
      top_adventure: topAdventure || null,
      latest_actions: latestActions,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/adventures', (req, res) => {
  try {
    const rows = db.query('SELECT * FROM adventures ORDER BY created_at DESC').all();
    res.json(rows.map(hydrateAdventure));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/adventures/:id', (req, res) => {
  try {
    const row = db.query('SELECT * FROM adventures WHERE id = ?').get(req.params.id) as any;
    if (!row) return res.status(404).json({ error: 'Adventure not found' });
    res.json(hydrateAdventure(row));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions', (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 24;
    const rows = db.query(`
      SELECT
        gs.id,
        gs.adventure_id,
        gs.created_at,
        gs.last_played,
        a.title as adventure_title,
        ps.location,
        ps.score,
        ps.hp,
        ps.max_hp,
        ps.currency,
        ps.game_day,
        ps.game_time
      FROM game_sessions gs
      JOIN player_state ps ON gs.id = ps.session_id
      JOIN adventures a ON gs.adventure_id = a.id
      ORDER BY gs.last_played DESC
      LIMIT ?
    `).all(limit) as any[];
    res.json(rows);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id', (req, res) => {
  try {
    const session = db.query('SELECT * FROM game_sessions WHERE id = ?').get(req.params.id) as any;
    if (!session) return res.status(404).json({ error: 'Session not found' });

    const stateRow = db.query('SELECT * FROM player_state WHERE session_id = ?').get(req.params.id) as any;
    const adventureRow = db.query('SELECT * FROM adventures WHERE id = ?').get(session.adventure_id) as any;

    const counts = {
      history: (db.query('SELECT COUNT(*) as c FROM action_history WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
      characters: (db.query('SELECT COUNT(*) as c FROM characters WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
      locations: (db.query('SELECT COUNT(*) as c FROM locations WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
      items: (db.query('SELECT COUNT(*) as c FROM items WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
      factions: (db.query('SELECT COUNT(*) as c FROM factions WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
      status_effects: (db.query('SELECT COUNT(*) as c FROM status_effects WHERE session_id = ?').get(req.params.id) as { c?: number } | undefined)?.c ?? 0,
    };

    res.json({
      id: session.id,
      adventure_id: session.adventure_id,
      created_at: session.created_at,
      last_played: session.last_played,
      state: hydrateState(stateRow),
      adventure: hydrateAdventure(adventureRow),
      counts,
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id/history', (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 50;
    const rows = db.query(
      'SELECT * FROM action_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?'
    ).all(req.params.id, limit) as any[];
    res.json(rows.map(hydrateHistory));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id/world', (req, res) => {
  try {
    res.json(loadWorld(req.params.id));
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id/summaries', (req, res) => {
  try {
    const rows = db.query('SELECT * FROM session_summaries WHERE session_id = ? ORDER BY created_at DESC').all(req.params.id)
      .map((r: any) => ({
        ...r,
        key_events: safeJson(r.key_events, []),
        character_changes: safeJson(r.character_changes, []),
      }));
    res.json(rows);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/sessions/:id/thoughts', (req, res) => {
  try {
    const rows = db.query('SELECT * FROM narrator_thoughts WHERE session_id = ? ORDER BY created_at DESC').all(req.params.id) as any[];
    res.json(rows);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default app;
