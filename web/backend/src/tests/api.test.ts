import request from 'supertest';
import app from '../app';
import db from '../db';

// Mock the db module
jest.mock('../db', () => {
  return {
    prepare: jest.fn(),
  };
});

describe('API Endpoints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('GET /api/health returns status ok', async () => {
    const res = await request(app).get('/api/health');
    expect(res.statusCode).toEqual(200);
    expect(res.body).toEqual({ status: 'ok' });
  });

  it('GET /api/adventures returns list of adventures', async () => {
    const mockAdventures = [
      { id: 'adv1', title: 'Test Adventure', stats: '[]', word_lists: '[]' }
    ];
    
    const mockStmt = {
        all: jest.fn().mockReturnValue(mockAdventures)
    };
    (db.prepare as jest.Mock).mockReturnValue(mockStmt);

    const res = await request(app).get('/api/adventures');
    expect(res.statusCode).toEqual(200);
    expect(res.body).toHaveLength(1);
    expect(res.body[0].title).toBe('Test Adventure');
    expect(db.prepare).toHaveBeenCalledWith('SELECT * FROM adventures');
  });

  it('GET /api/sessions returns list of sessions', async () => {
      const mockSessions = [
          { id: 'sess1', adventure_title: 'Test Adv', score: 100 }
      ];
      const mockStmt = {
          all: jest.fn().mockReturnValue(mockSessions)
      };
      (db.prepare as jest.Mock).mockReturnValue(mockStmt);

      const res = await request(app).get('/api/sessions');
      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveLength(1);
      expect(res.body[0].id).toBe('sess1');
  });

  it('GET /api/sessions/:id returns session details', async () => {
      const mockSession = { id: 'sess1', adventure_id: 'adv1' };
      const mockState = { 
          session_id: 'sess1', 
          hp: 10, 
          stats: '{"strength": 10}',
          inventory: '[]',
          quests: '[]'
      };
      const mockAdventure = { id: 'adv1', title: 'Test Adv', stats: '[]' };

      const mockSessionStmt = { get: jest.fn().mockReturnValue(mockSession) };
      const mockStateStmt = { get: jest.fn().mockReturnValue(mockState) };
      const mockAdvStmt = { get: jest.fn().mockReturnValue(mockAdventure) };

      (db.prepare as jest.Mock)
        .mockReturnValueOnce(mockSessionStmt)
        .mockReturnValueOnce(mockStateStmt)
        .mockReturnValueOnce(mockAdvStmt);

      const res = await request(app).get('/api/sessions/sess1');
      expect(res.statusCode).toEqual(200);
      expect(res.body.id).toBe('sess1');
      expect(res.body.state.hp).toBe(10);
      expect(res.body.adventure.title).toBe('Test Adv');
  });

  it('GET /api/sessions/:id/history returns history log', async () => {
      const mockHistory = [
          { action_text: 'Hit goblin', dice_roll: '{"roll": 20}' }
      ];
      const mockStmt = {
          all: jest.fn().mockReturnValue(mockHistory)
      };
      (db.prepare as jest.Mock).mockReturnValue(mockStmt);

      const res = await request(app).get('/api/sessions/sess1/history');
      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveLength(1);
      expect(res.body[0].dice_roll.roll).toBe(20);
  });
});
