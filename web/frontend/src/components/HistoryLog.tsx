import { Box, Paper, Typography, Chip, Divider } from '@mui/material';
import type { ActionHistory } from '../types';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import CasinoIcon from '@mui/icons-material/Casino';

interface HistoryLogProps {
    history: ActionHistory[];
}

export default function HistoryLog({ history }: HistoryLogProps) {
    return (
        <Paper sx={{ p: 2, height: '70vh', overflowY: 'auto', bgcolor: 'background.paper' }}>
            <Typography variant="h6" gutterBottom sx={{ position: 'sticky', top: 0, bgcolor: 'background.paper', zIndex: 1, pb: 1 }}>
                Adventure Log
            </Typography>
            {history.map((entry, index) => (
                <Box key={index} sx={{ mb: 3 }}>
                    {/* Player Action */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" color="primary" sx={{ mr: 1, fontWeight: 'bold' }}>
                            You:
                        </Typography>
                        <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                            {entry.action_text}
                        </Typography>
                    </Box>

                    {/* Dice Roll Info if present */}
                    {entry.dice_roll.roll > 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, ml: 2, opacity: 0.8 }}>
                            <CasinoIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                                Rolled {entry.dice_roll.roll} {entry.dice_roll.modifier >= 0 ? '+' : ''}{entry.dice_roll.modifier} = {entry.dice_roll.total}
                            </Typography>
                            {entry.dice_roll.success !== undefined && (
                                <Chip 
                                    icon={entry.dice_roll.success ? <CheckCircleIcon /> : <CancelIcon />}
                                    label={entry.dice_roll.success ? "Success" : "Failure"}
                                    size="small"
                                    color={entry.dice_roll.success ? "success" : "error"}
                                    variant="outlined"
                                    sx={{ ml: 1, height: 20 }}
                                />
                            )}
                        </Box>
                    )}

                    {/* Narrator Outcome */}
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 2, borderLeft: 4, borderColor: 'secondary.main' }}>
                        <Typography variant="body1">
                            {entry.outcome}
                        </Typography>
                        {entry.score_change !== 0 && (
                            <Typography variant="caption" display="block" sx={{ mt: 1, color: entry.score_change > 0 ? 'success.main' : 'error.main' }}>
                                Score {entry.score_change > 0 ? '+' : ''}{entry.score_change}
                            </Typography>
                        )}
                    </Paper>
                    
                    <Divider sx={{ mt: 2, opacity: 0.3 }} />
                </Box>
            ))}
        </Paper>
    );
}