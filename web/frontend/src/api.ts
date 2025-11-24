import axios from 'axios';
import type { GameSession, ActionHistory, Adventure } from './types';

// Use relative path so it goes through the same host/port (Nginx proxy in Docker, or Vite proxy in Dev)
const API_BASE_URL = '/api';

export const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getAdventures = async (): Promise<Adventure[]> => {
    const response = await api.get('/adventures');
    return response.data;
};

export const getRecentSessions = async (limit = 20): Promise<GameSession[]> => {
    const response = await api.get(`/sessions?limit=${limit}`);
    return response.data;
};

export const getSessionDetails = async (id: string): Promise<GameSession> => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
};

export const getSessionHistory = async (id: string, limit = 50): Promise<ActionHistory[]> => {
    const response = await api.get(`/sessions/${id}/history?limit=${limit}`);
    return response.data;
};
