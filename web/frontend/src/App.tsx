import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CssBaseline, ThemeProvider, Box, AppBar, Toolbar, Typography, IconButton, Container } from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useAppStore } from './store';
import { getTheme } from './theme';
import Home from './pages/Home';
import SessionView from './pages/SessionView';

const queryClient = new QueryClient();

function AppContent() {
    const { darkMode, toggleDarkMode, currentAdventureTheme } = useAppStore();
    const theme = React.useMemo(() => getTheme(darkMode ? 'dark' : 'light', currentAdventureTheme || undefined), [darkMode, currentAdventureTheme]);

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
                <AppBar position="static" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
                    <Toolbar>
                        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold', color: 'primary.main' }}>
                            Adventure Handler
                        </Typography>
                        <IconButton sx={{ ml: 1 }} onClick={toggleDarkMode} color="inherit">
                            {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
                        </IconButton>
                    </Toolbar>
                </AppBar>
                <Container component="main" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
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
                <AppContent />
            </Router>
        </QueryClientProvider>
    );
}