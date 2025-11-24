import { useQuery } from '@tanstack/react-query';
import { Grid, Card, CardContent, Typography, CardActionArea, Chip, Box, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { getRecentSessions } from '../api';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import SportsScoreIcon from '@mui/icons-material/SportsScore';

export default function Home() {
    const navigate = useNavigate();
    const { data: sessions, isLoading, error } = useQuery({
        queryKey: ['sessions'],
        queryFn: () => getRecentSessions(20)
    });

    if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
    if (error) return <Typography color="error">Error loading sessions</Typography>;

    return (
        <Box>
            <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
                Recent Adventures
            </Typography>
            <Grid container spacing={3}>
                {sessions?.map((session) => (
                    <Grid size={{ xs: 12, sm: 6, md: 4 }} key={session.id}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                            <CardActionArea onClick={() => navigate(`/session/${session.id}`)} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'flex-start' }}>
                                <CardContent sx={{ width: '100%' }}>
                                    <Typography variant="overline" color="text.secondary">
                                        {session.id}
                                    </Typography>
                                    <Typography variant="h5" component="div" gutterBottom color="primary">
                                        {session.adventure_title || 'Unknown Adventure'}
                                    </Typography>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                        <SportsScoreIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                                        <Typography variant="body2" color="text.secondary">
                                            Score: {session.state?.score ?? 'N/A'}
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                        <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                                        <Typography variant="body2" color="text.secondary">
                                            {new Date(session.last_played).toLocaleDateString()}
                                        </Typography>
                                    </Box>
                                    <Chip 
                                        label={session.state?.location || 'Unknown Location'} 
                                        size="small" 
                                        color="secondary" 
                                        variant="outlined" 
                                    />
                                </CardContent>
                            </CardActionArea>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}