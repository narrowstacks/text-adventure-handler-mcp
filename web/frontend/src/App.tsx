import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
    CssBaseline,
    ThemeProvider,
    Box,
    AppBar,
    Toolbar,
    Typography,
    IconButton,
    Container,
    Stack,
    Chip,
} from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import ExploreIcon from '@mui/icons-material/Explore';
import Home from './pages/Home';
import SessionView from './pages/SessionView';
import { useAppStore } from './store';
import { getTheme } from './theme';
import './App.css';

const queryClient = new QueryClient();

function AppChrome() {
    const { darkMode, toggleDarkMode, currentAdventureTheme } = useAppStore();
    const theme = React.useMemo(
        () => getTheme(darkMode ? 'dark' : 'light', currentAdventureTheme || undefined),
        [darkMode, currentAdventureTheme]
    );

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }} className="grainy">
                <AppBar position="sticky" elevation={0} color="transparent" sx={{ backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <Toolbar sx={{ gap: 2 }}>
                        <Stack direction="row" alignItems="center" spacing={1} component={Link} to="/" sx={{ color: 'inherit' }}>
                            <ExploreIcon color="secondary" />
                            <Box>
                                <Typography variant="subtitle2" sx={{ opacity: 0.75 }}>
                                    Text Adventure
                                </Typography>
                                <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1 }}>
                                    Command Console
                                </Typography>
                            </Box>
                        </Stack>
                        <Chip
                            label="MCP-synced"
                            size="small"
                            color="secondary"
                            sx={{ ml: 2, fontWeight: 600, letterSpacing: 0.2 }}
                        />
                        <Box sx={{ flexGrow: 1 }} />
                        <Stack direction="row" spacing={3} alignItems="center">
                            <Link to="/" style={{ color: 'inherit', fontWeight: 600 }}>Dashboard</Link>
                            <Link to="/" style={{ color: 'inherit', fontWeight: 600 }}>Adventures</Link>
                        </Stack>
                        <IconButton sx={{ ml: 1 }} onClick={toggleDarkMode} color="inherit">
                            {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
                        </IconButton>
                    </Toolbar>
                </AppBar>
                <Container sx={{ py: 4 }}>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/session/:id" element={<SessionView />} />
                    </Routes>
                </Container>
            </Box>
        </ThemeProvider>
    );
}

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <AppChrome />
            </Router>
        </QueryClientProvider>
    );
}
