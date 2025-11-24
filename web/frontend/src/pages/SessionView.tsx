import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Grid, Box, Typography, LinearProgress, Card, CardContent, CircularProgress } from '@mui/material';
import { getSessionDetails, getSessionHistory } from '../api';
import { useAppStore } from '../store';
import HistoryLog from '../components/HistoryLog';
import QuestTracker from '../components/QuestTracker';
import InventoryList from '../components/InventoryList';
import FavoriteIcon from '@mui/icons-material/Favorite';
import LocationOnIcon from '@mui/icons-material/LocationOn';

export default function SessionView() {
    const { id } = useParams<{ id: string }>();
    const { setAdventureTheme } = useAppStore();

    const { data: session, isLoading: sessionLoading } = useQuery({
        queryKey: ['session', id],
        queryFn: () => getSessionDetails(id!),
        enabled: !!id,
        refetchInterval: 2000 // Poll every 2 seconds for updates
    });

    const { data: history, isLoading: historyLoading } = useQuery({
        queryKey: ['history', id],
        queryFn: () => getSessionHistory(id!),
        enabled: !!id,
        refetchInterval: 2000
    });

    useEffect(() => {
        if (session?.adventure_title) {
            setAdventureTheme(session.adventure_title);
        }
        return () => setAdventureTheme(null);
    }, [session, setAdventureTheme]);

    if (sessionLoading || historyLoading) return <Box sx={{ width: '100%', mt: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>;
    if (!session) return <Typography>Session not found</Typography>;

    const state = session.state;
    if (!state) return <Typography>No state found for this session.</Typography>;

    return (
        <Box>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="overline" color="text.secondary">Adventure: {session.adventure?.title}</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                    <Typography variant="h3" sx={{ fontWeight: 'bold', mr: 2 }}>
                        Session {session.id.substring(0, 8)}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LocationOnIcon color="error" sx={{ mr: 1 }} />
                        <Typography variant="h6">{state.location}</Typography>
                    </Box>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Left Column: Stats & Character */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Card sx={{ mb: 2 }}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Vitality</Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <FavoriteIcon color="error" sx={{ mr: 1 }} />
                                <Typography variant="h5">{state.hp} / {state.max_hp}</Typography>
                            </Box>
                            <LinearProgress 
                                variant="determinate" 
                                value={(state.hp / state.max_hp) * 100} 
                                color="error" 
                                sx={{ height: 10, borderRadius: 5 }}
                            />
                        </CardContent>
                    </Card>

                    <Card sx={{ mb: 2 }}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Stats</Typography>
                            {Object.entries(state.stats).map(([key, value]) => (
                                <Box key={key} sx={{ mb: 1 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{key}</Typography>
                                        <Typography variant="body2" fontWeight="bold">{value}</Typography>
                                    </Box>
                                    <LinearProgress variant="determinate" value={(value / 20) * 100} sx={{ height: 6, borderRadius: 3, mt: 0.5, opacity: 0.7 }} />
                                </Box>
                            ))}
                        </CardContent>
                    </Card>

                    <InventoryList inventory={state.inventory} />
                </Grid>

                {/* Center Column: History Log */}
                <Grid size={{ xs: 12, md: 6 }}>
                    <HistoryLog history={history || []} />
                </Grid>

                {/* Right Column: Quests & Info */}
                <Grid size={{ xs: 12, md: 3 }}>
                     <QuestTracker quests={state.quests} />
                     
                     <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>Details</Typography>
                            <Typography variant="body2" color="text.secondary">
                                <strong>Score:</strong> {state.score}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                <strong>Day:</strong> {state.game_day}
                            </Typography>
                             <Typography variant="body2" color="text.secondary">
                                <strong>Time:</strong> {state.game_time}:00
                            </Typography>
                            {state.currency > 0 && (
                                <Typography variant="body2" color="text.secondary">
                                    <strong>Gold:</strong> {state.currency}
                                </Typography>
                            )}
                        </CardContent>
                     </Card>
                </Grid>
            </Grid>
        </Box>
    );
}