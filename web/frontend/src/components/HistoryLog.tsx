import { Box, Typography, Paper, Stack } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import type { ActionHistory, SkillCheckData, DiceRollData } from '../types';
import DiceRoll from './DiceRoll';
import SkillCheck from './SkillCheck';
import { useReducedMotion, listItemEntrance } from '../utils/animations';

// Type guard to check if the roll data is a skill check
function isSkillCheck(data: ActionHistory['dice_roll']): data is SkillCheckData {
    return data && 'type' in data && data.type === 'skill_check';
}

// Type guard to check if the roll data is a dice roll
function isDiceRoll(data: ActionHistory['dice_roll']): data is DiceRollData {
    return data && 'roll' in data && typeof data.roll === 'number';
}

interface HistoryLogProps {
    history: ActionHistory[];
}

export default function HistoryLog({ history }: HistoryLogProps) {
    const reducedMotion = useReducedMotion();

    return (
        <Box sx={{ maxHeight: '60vh', overflowY: 'auto', pr: 1 }}>
            <AnimatePresence mode="popLayout">
                {history.map((entry, index) => {
                    const rollData = entry.dice_roll;
                    const isSkillCheckEntry = isSkillCheck(rollData);
                    const isDiceRollEntry = isDiceRoll(rollData);

                    const isCritical = isDiceRollEntry && (rollData.roll === 20 || rollData.roll === 1);
                    const isSuccess = rollData?.success;

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
                                        ? isDiceRollEntry && rollData.roll === 20
                                            ? 'linear-gradient(135deg, rgba(124,231,194,0.12), rgba(124,231,194,0.04))'
                                            : 'linear-gradient(135deg, rgba(255,107,107,0.12), rgba(255,107,107,0.04))'
                                        : isSkillCheckEntry
                                          ? isSuccess
                                              ? 'linear-gradient(135deg, rgba(124,231,194,0.08), rgba(124,231,194,0.02))'
                                              : 'linear-gradient(135deg, rgba(255,107,107,0.08), rgba(255,107,107,0.02))'
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

                                {isSkillCheckEntry && (
                                    <Box sx={{ my: 1 }}>
                                        <SkillCheck
                                            statValue={rollData.stat_value}
                                            threshold={rollData.threshold}
                                            margin={rollData.margin}
                                            success={rollData.success}
                                            statUsed={entry.stat_used}
                                            reason={rollData.reason}
                                        />
                                    </Box>
                                )}

                                {isDiceRollEntry && (
                                    <Box sx={{ my: 1 }}>
                                        <DiceRoll
                                            roll={rollData.roll!}
                                            total={rollData.total ?? rollData.roll!}
                                            modifier={rollData.modifier}
                                            dc={rollData.dc}
                                            success={rollData.success}
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
