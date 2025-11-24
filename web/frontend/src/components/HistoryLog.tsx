import { Box, Typography, Paper, Stack } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import type { ActionHistory } from '../types';
import DiceRoll from './DiceRoll';
import { useReducedMotion, listItemEntrance } from '../utils/animations';

interface HistoryLogProps {
    history: ActionHistory[];
}

export default function HistoryLog({ history }: HistoryLogProps) {
    const reducedMotion = useReducedMotion();

    return (
        <Box sx={{ maxHeight: '60vh', overflowY: 'auto', pr: 1 }}>
            <AnimatePresence mode="popLayout">
                {history.map((entry, index) => {
                    const isCritical = entry.dice_roll?.roll === 20 || entry.dice_roll?.roll === 1;
                    const isSuccess = entry.dice_roll?.success;

                    return (
                        <motion.div
                            key={entry.id || `${entry.timestamp}-${index}`}
                            variants={listItemEntrance}
                            initial={reducedMotion ? false : 'hidden'}
                            animate="visible"
                            exit="exit"
                            layout
                        >
                            <Paper
                                variant="outlined"
                                sx={{
                                    mb: 1.5,
                                    p: 1.5,
                                    background: isCritical
                                        ? entry.dice_roll?.roll === 20
                                            ? 'linear-gradient(135deg, rgba(124,231,194,0.12), rgba(124,231,194,0.04))'
                                            : 'linear-gradient(135deg, rgba(255,107,107,0.12), rgba(255,107,107,0.04))'
                                        : 'linear-gradient(135deg, rgba(124,231,194,0.04), rgba(255,138,167,0.04))',
                                    borderLeft: '3px solid',
                                    borderColor: isSuccess === undefined
                                        ? 'secondary.main'
                                        : isSuccess
                                          ? 'success.main'
                                          : 'error.main',
                                    transition: 'all 0.3s ease',
                                    '&:hover': {
                                        background: 'linear-gradient(135deg, rgba(124,231,194,0.08), rgba(255,138,167,0.08))'
                                    }
                                }}
                            >
                                <Stack direction="row" spacing={1} alignItems="flex-start" sx={{ mb: 0.5 }}>
                                    <Typography variant="subtitle2" color="primary" sx={{ flexShrink: 0 }}>
                                        You:
                                    </Typography>
                                    <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                                        {entry.action_text}
                                    </Typography>
                                </Stack>

                                {entry.dice_roll?.roll && (
                                    <Box sx={{ my: 1 }}>
                                        <DiceRoll
                                            roll={entry.dice_roll.roll}
                                            total={entry.dice_roll.total ?? entry.dice_roll.roll}
                                            modifier={entry.dice_roll.modifier}
                                            dc={entry.dice_roll.dc}
                                            success={entry.dice_roll.success}
                                            statUsed={entry.stat_used}
                                        />
                                    </Box>
                                )}

                                {entry.outcome && (
                                    <Typography variant="body2" sx={{ mb: 0.5, lineHeight: 1.6 }}>
                                        {entry.outcome}
                                    </Typography>
                                )}

                                {entry.score_change !== undefined && entry.score_change !== 0 && (
                                    <motion.div
                                        initial={reducedMotion ? {} : { scale: 0.8, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        transition={{ type: 'spring', stiffness: 400, damping: 15 }}
                                        style={{ display: 'inline-block', marginTop: 4 }}
                                    >
                                        <Typography
                                            variant="caption"
                                            sx={{
                                                color: entry.score_change > 0 ? '#7ce7c2' : '#ff6b6b',
                                                fontWeight: 700,
                                                fontSize: '0.8rem',
                                                textShadow:
                                                    entry.score_change > 0
                                                        ? '0 0 10px rgba(124, 231, 194, 0.5)'
                                                        : '0 0 10px rgba(255, 107, 107, 0.5)'
                                            }}
                                        >
                                            Score {entry.score_change > 0 ? '+' : ''}
                                            {entry.score_change}
                                        </Typography>
                                    </motion.div>
                                )}
                            </Paper>
                        </motion.div>
                    );
                })}
            </AnimatePresence>
        </Box>
    );
}
