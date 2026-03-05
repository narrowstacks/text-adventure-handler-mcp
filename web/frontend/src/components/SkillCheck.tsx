import { motion } from 'framer-motion';
import { Box, Typography, Chip } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { useReducedMotion } from '../utils/animations';

interface SkillCheckProps {
    statValue: number;
    threshold: number;
    margin: number;
    success: boolean;
    statUsed?: string;
    reason?: string;
    compact?: boolean;
}

export default function SkillCheck({
    statValue,
    threshold,
    margin,
    success,
    statUsed,
    reason,
    compact = false
}: SkillCheckProps) {
    const reducedMotion = useReducedMotion();

    const resultColor = success ? '#7ce7c2' : '#ff6b6b';
    const glowColor = success ? 'rgba(124, 231, 194, 0.6)' : 'rgba(255, 107, 107, 0.6)';

    if (compact) {
        return (
            <motion.div
                initial={reducedMotion ? {} : { scale: 0.8, opacity: 0 }}
                animate={reducedMotion ? {} : { scale: 1, opacity: 1 }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
                <CheckCircleOutlineIcon sx={{ fontSize: 16, color: resultColor }} />
                <Typography
                    variant="caption"
                    sx={{
                        fontWeight: 600,
                        color: resultColor
                    }}
                >
                    {statValue} vs {threshold}
                </Typography>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={reducedMotion ? {} : { scale: 0.95, opacity: 0 }}
            animate={reducedMotion ? {} : { scale: 1, opacity: 1 }}
            transition={{
                type: 'spring',
                stiffness: 300,
                damping: 20
            }}
        >
            <Box
                sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 1,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 2,
                    bgcolor: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: `0 0 12px ${glowColor}`,
                    transition: 'box-shadow 0.3s ease'
                }}
            >
                <motion.div
                    animate={
                        reducedMotion
                            ? {}
                            : {
                                  scale: [1, 1.15, 1]
                              }
                    }
                    transition={{ duration: 0.4, ease: 'easeOut' }}
                    style={{ display: 'flex', alignItems: 'center' }}
                >
                    <CheckCircleOutlineIcon
                        sx={{
                            fontSize: 20,
                            color: resultColor
                        }}
                    />
                </motion.div>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                    <Typography
                        variant="body2"
                        sx={{
                            fontWeight: 700,
                            fontSize: '1.1rem',
                            color: resultColor
                        }}
                    >
                        {statValue}
                    </Typography>

                    <Typography variant="caption" color="text.secondary">
                        vs {threshold}
                    </Typography>

                    {margin !== 0 && (
                        <Typography
                            variant="caption"
                            sx={{
                                color: margin > 0 ? '#7ce7c2' : '#ff6b6b',
                                fontWeight: 600
                            }}
                        >
                            ({margin > 0 ? '+' : ''}{margin})
                        </Typography>
                    )}
                </Box>

                {statUsed && (
                    <Chip
                        label={statUsed}
                        size="small"
                        sx={{
                            height: 20,
                            fontSize: '0.65rem',
                            bgcolor: 'rgba(124, 231, 194, 0.15)',
                            ml: 0.5
                        }}
                    />
                )}

                <Chip
                    label={success ? 'PASSED' : 'FAILED'}
                    size="small"
                    sx={{
                        height: 20,
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        bgcolor: success ? 'rgba(124, 231, 194, 0.2)' : 'rgba(255, 107, 107, 0.2)',
                        color: resultColor,
                        ml: 0.5
                    }}
                />

                <Chip
                    label="SKILL"
                    size="small"
                    variant="outlined"
                    sx={{
                        height: 18,
                        fontSize: '0.55rem',
                        fontWeight: 600,
                        borderColor: 'rgba(255,255,255,0.2)',
                        color: 'text.secondary',
                        ml: 0.5
                    }}
                />

                {success && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [0, 1.2, 1] }}
                        transition={{ delay: 0.2, duration: 0.3 }}
                    >
                        <Typography sx={{ fontSize: '0.85rem' }}>✓</Typography>
                    </motion.div>
                )}
            </Box>

            {reason && (
                <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block', mt: 0.5, fontStyle: 'italic', opacity: 0.7 }}
                >
                    {reason}
                </Typography>
            )}
        </motion.div>
    );
}
