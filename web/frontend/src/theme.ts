import { createTheme, type ThemeOptions } from '@mui/material/styles';

export const getTheme = (mode: 'light' | 'dark', adventureTitle?: string) => {
    let primaryColor = '#90caf9'; // Default Blue
    let secondaryColor = '#f48fb1'; // Default Pink

    if (adventureTitle) {
        const title = adventureTitle.toLowerCase();
        if (title.includes('fantasy') || title.includes('dungeon') || title.includes('dragon') || title.includes('sword')) {
            primaryColor = '#d4af37'; // Gold
            secondaryColor = '#8b0000'; // Dark Red
        } else if (title.includes('sci-fi') || title.includes('space') || title.includes('cyber') || title.includes('void') || title.includes('station')) {
            primaryColor = '#00e5ff'; // Cyan
            secondaryColor = '#76ff03'; // Neon Green
        } else if (title.includes('noir') || title.includes('detective') || title.includes('mystery')) {
            primaryColor = '#cfcfcf'; // Silver
            secondaryColor = '#ffca28'; // Amber (streetlights)
        } else if (title.includes('horror') || title.includes('cursed') || title.includes('ghost')) {
            primaryColor = '#b388ff'; // Deep Purple
            secondaryColor = '#ff5252'; // Red
        }
    }

    const themeOptions: ThemeOptions = {
        palette: {
            mode,
            primary: {
                main: primaryColor,
            },
            secondary: {
                main: secondaryColor,
            },
            background: {
                default: mode === 'dark' ? '#121212' : '#f5f5f5',
                paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
            },
        },
        typography: {
            fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
            h4: {
                fontWeight: 600,
            },
            h6: {
                fontWeight: 500,
            },
        },
        components: {
            MuiCard: {
                styleOverrides: {
                    root: {
                        backgroundImage: 'none', // Remove default gradient in dark mode
                        borderRadius: 12,
                        boxShadow: mode === 'dark' ? '0 4px 6px rgba(0,0,0,0.3)' : '0 4px 6px rgba(0,0,0,0.1)',
                    },
                },
            },
        },
    };

    return createTheme(themeOptions);
};