import express from 'express';
import cors from 'cors';
import db from './db';

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Get all adventures
app.get('/api/adventures', (req, res) => {
  try {
    const stmt = db.prepare('SELECT * FROM adventures');
    const adventures = stmt.all();
    // Parse JSON fields
    const parsedAdventures = adventures.map((adv: any) => ({
      ...adv,
      stats: JSON.parse(adv.stats || '[]'),
      word_lists: JSON.parse(adv.word_lists || '[]'),
      features: JSON.parse(adv.features || '{}'),
      time_config: JSON.parse(adv.time_config || '{}'),
      currency_config: JSON.parse(adv.currency_config || '{}'),
      factions: JSON.parse(adv.factions || '[]')
    }));
    res.json(parsedAdventures);
  } catch (error: any) {
    console.error('Error fetching adventures:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get recent sessions
app.get('/api/sessions', (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 20;
    const stmt = db.prepare(`
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
    `);
    const sessions = stmt.all(limit);
    res.json(sessions);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get specific session details (dashboard data)
app.get('/api/sessions/:id', (req, res) => {
  try {
    const { id } = req.params;
    const sessionStmt = db.prepare('SELECT * FROM game_sessions WHERE id = ?');
    const session = sessionStmt.get(id) as any;
    
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }

    const stateStmt = db.prepare('SELECT * FROM player_state WHERE session_id = ?');
    const state = stateStmt.get(id) as any;

    if (state) {
      // Parse JSON fields in state
      state.stats = JSON.parse(state.stats || '{}');
      state.inventory = JSON.parse(state.inventory || '[]');
      state.quests = JSON.parse(state.quests || '[]');
      state.relationships = JSON.parse(state.relationships || '{}');
      state.custom_data = JSON.parse(state.custom_data || '{}');
    }

    const adventureStmt = db.prepare('SELECT * FROM adventures WHERE id = ?');
    const adventure = adventureStmt.get(session.adventure_id) as any;
    
    if (adventure) {
        adventure.stats = JSON.parse(adventure.stats || '[]');
        // Parse other adventure fields if needed for themeing
    }

    res.json({ ...session, state, adventure });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get session history
app.get('/api/sessions/:id/history', (req, res) => {
  try {
    const { id } = req.params;
    const limit = req.query.limit ? parseInt(req.query.limit as string) : 50;
    const stmt = db.prepare(`
      SELECT * FROM action_history 
      WHERE session_id = ? 
      ORDER BY timestamp DESC 
      LIMIT ?
    `);
    const history = stmt.all(id, limit);
    
    // Parse JSON dice_roll
    const parsedHistory = history.map((h: any) => ({
      ...h,
      dice_roll: JSON.parse(h.dice_roll || '{}')
    }));

    res.json(parsedHistory); 
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default app;
