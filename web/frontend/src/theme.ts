import { createTheme, type ThemeOptions } from '@mui/material/styles';

// Gaming color palette
export const gameColors = {
    hp: '#ff6b6b',
    hpGlow: 'rgba(255, 107, 107, 0.5)',
    mana: '#5fe0ff',
    manaGlow: 'rgba(95, 224, 255, 0.5)',
    gold: '#f0c75e',
    goldGlow: 'rgba(240, 199, 94, 0.5)',
    xp: '#c792ea',
    xpGlow: 'rgba(199, 146, 234, 0.5)',
    success: '#7ce7c2',
    successGlow: 'rgba(124, 231, 194, 0.5)',
    error: '#ff6b6b',
    errorGlow: 'rgba(255, 107, 107, 0.5)',
};

// Animation presets
export const animationPresets = {
    cardHover: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
    fadeIn: 'opacity 0.3s ease-out',
    slideUp: 'transform 0.4s ease-out, opacity 0.4s ease-out',
    pulse: 'all 0.3s ease-in-out',
    glow: 'box-shadow 0.3s ease-in-out',
};

export const getTheme = (mode: 'light' | 'dark', accent?: string) => {
    const primary = mode === 'dark' ? '#7ce7c2' : '#0e9f6e';
    const secondary = mode === 'dark' ? '#ff8ba7' : '#c5226f';
    const accentColor =
        accent?.toLowerCase().includes('space') || accent?.toLowerCase().includes('cyber')
            ? '#5fe0ff'
            : accent?.toLowerCase().includes('dungeon') || accent?.toLowerCase().includes('dragon')
            ? '#f0c75e'
            : secondary;

    const themeOptions: ThemeOptions = {
        palette: {
            mode,
            primary: { main: primary },
            secondary: { main: accentColor },
            background: {
                default: mode === 'dark' ? '#0c0f12' : '#f6f7fb',
                paper: mode === 'dark' ? 'rgba(18,22,28,0.85)' : '#ffffff',
            },
            success: { main: gameColors.success },
            error: { main: gameColors.error },
            warning: { main: gameColors.gold },
            info: { main: gameColors.mana },
        },
        shape: { borderRadius: 14 },
        typography: {
            fontFamily: `'Space Grotesk', 'Manrope', system-ui, sans-serif`,
            h3: { fontWeight: 700, letterSpacing: '-0.02em' },
            h4: { fontWeight: 700 },
            h6: { fontWeight: 600 },
            body2: { color: mode === 'dark' ? '#c7cbd6' : '#4a4d57' },
        },
        components: {
            MuiCard: {
                styleOverrides: {
                    root: {
                        border: mode === 'dark' ? '1px solid rgba(255,255,255,0.05)' : '1px solid #e6e8ef',
                        boxShadow:
                            mode === 'dark'
                                ? '0 16px 50px rgba(0,0,0,0.35)'
                                : '0 12px 40px rgba(15,23,42,0.08)',
                        backdropFilter: 'blur(6px)',
                        transition: animationPresets.cardHover,
                    },
                },
            },
            MuiAppBar: {
                styleOverrides: {
                    root: {
                        background: 'linear-gradient(90deg, rgba(16,24,40,0.95), rgba(12,12,18,0.95))',
                        backdropFilter: 'blur(10px)',
                    },
                },
            },
            MuiContainer: {
                defaultProps: {
                    maxWidth: 'xl',
                },
            },
            MuiChip: {
                styleOverrides: {
                    root: {
                        transition: 'all 0.2s ease',
                    },
                },
            },
            MuiLinearProgress: {
                styleOverrides: {
                    root: {
                        borderRadius: 4,
                        backgroundColor: 'rgba(255,255,255,0.1)',
                    },
                    bar: {
                        borderRadius: 4,
                        transition: 'transform 0.5s ease-in-out',
                    },
                },
            },
            MuiButton: {
                styleOverrides: {
                    root: {
                        textTransform: 'none',
                        fontWeight: 600,
                        transition: 'all 0.2s ease',
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: {
                        transition: animationPresets.cardHover,
                    },
                },
            },
        },
    };

    return createTheme(themeOptions);
};
