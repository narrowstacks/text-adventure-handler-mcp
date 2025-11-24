import axios from 'axios';
import type {
    Adventure,
    DashboardData,
    GameSessionDetail,
    GameSessionListItem,
    ActionHistory,
    WorldState,
    SessionSummaryRecord,
    NarratorThoughtRecord,
} from './types';

const api = axios.create({ baseURL: '/api' });

export const getDashboard = async (): Promise<DashboardData> => {
    const res = await api.get('/dashboard');
    return res.data;
};

export const getAdventures = async (): Promise<Adventure[]> => {
    const res = await api.get('/adventures');
    return res.data;
};

export const getSessions = async (limit = 24): Promise<GameSessionListItem[]> => {
    const res = await api.get(`/sessions?limit=${limit}`);
    return res.data;
};

export const getSession = async (id: string): Promise<GameSessionDetail> => {
    const res = await api.get(`/sessions/${id}`);
    return res.data;
};

export const getSessionHistory = async (id: string, limit = 120): Promise<ActionHistory[]> => {
    const res = await api.get(`/sessions/${id}/history?limit=${limit}`);
    return res.data;
};

export const getSessionWorld = async (id: string): Promise<WorldState> => {
    const res = await api.get(`/sessions/${id}/world`);
    return res.data;
};

export const getSessionSummaries = async (id: string): Promise<SessionSummaryRecord[]> => {
    const res = await api.get(`/sessions/${id}/summaries`);
    return res.data;
};

export const getNarratorThoughts = async (id: string): Promise<NarratorThoughtRecord[]> => {
    const res = await api.get(`/sessions/${id}/thoughts`);
    return res.data;
};
