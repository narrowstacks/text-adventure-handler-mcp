import { create } from 'zustand';

interface AppState {
    darkMode: boolean;
    toggleDarkMode: () => void;
    currentAdventureTheme: string | null;
    setAdventureTheme: (theme: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
    darkMode: true,
    toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
    currentAdventureTheme: null,
    setAdventureTheme: (theme) => set({ currentAdventureTheme: theme }),
}));
