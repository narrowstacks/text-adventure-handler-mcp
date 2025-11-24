import { motion } from 'framer-motion';
import { Box, Typography, Chip } from '@mui/material';
import CasinoIcon from '@mui/icons-material/Casino';
import { useReducedMotion } from '../utils/animations';

interface DiceRollProps {
    roll: number;
    total: number;
    modifier?: number;
    dc?: number;
    success?: boolean;
    statUsed?: string;
    compact?: boolean;
}

export default function DiceRoll({
    roll,
    total,
    modifier = 0,
    dc,
    success,
    statUsed,
    compact = false
}: DiceRollProps) {
    const reducedMotion = useReducedMotion();

    const isCriticalSuccess = roll === 20;
    const isCriticalFailure = roll === 1;
    const isCritical = isCriticalSuccess || isCriticalFailure;

    const glowColor = isCriticalSuccess
        ? 'rgba(124, 231, 194, 0.8)'
        : isCriticalFailure
          ? 'rgba(255, 107, 107, 0.8)'
          : 'transparent';

    const resultColor = success ? '#7ce7c2' : success === false ? '#ff6b6b' : 'inherit';

    if (compact) {
        return (
            <motion.div
                initial={reducedMotion ? {} : { scale: 0.8, opacity: 0 }}
                animate={reducedMotion ? {} : { scale: 1, opacity: 1 }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
                <CasinoIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography
                    variant="caption"
                    sx={{
                        fontWeight: 600,
                        color: resultColor,
                        textShadow: isCritical ? `0 0 10px ${glowColor}` : 'none'
                    }}
                >
                    {total}
                </Typography>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={reducedMotion ? {} : { scale: 0.8, opacity: 0, rotate: -10 }}
            animate={
                reducedMotion
                    ? {}
                    : {
                          scale: 1,
                          opacity: 1,
                          rotate: 0
                      }
            }
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
                    boxShadow: isCritical ? `0 0 20px ${glowColor}` : 'none',
                    transition: 'box-shadow 0.3s ease'
                }}
            >
                <motion.div
                    animate={
                        reducedMotion
                            ? {}
                            : {
                                  rotate: [0, 360],
                                  scale: [1, 1.1, 1]
                              }
                    }
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    style={{ display: 'flex', alignItems: 'center' }}
                >
                    <CasinoIcon
                        sx={{
                            fontSize: 20,
                            color: isCritical ? glowColor : 'primary.main'
                        }}
                    />
                </motion.div>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                    <Typography
                        variant="body2"
                        sx={{
                            fontWeight: 700,
                            fontSize: '1.1rem',
                            color: resultColor,
                            textShadow: isCritical ? `0 0 10px ${glowColor}` : 'none'
                        }}
                    >
                        {total}
                    </Typography>

                    <Typography variant="caption" color="text.secondary">
                        ({roll}
                        {modifier !== 0 && (
                            <span style={{ color: modifier > 0 ? '#7ce7c2' : '#ff6b6b' }}>
                                {modifier > 0 ? '+' : ''}
                                {modifier}
                            </span>
                        )}
                        )
                    </Typography>
                </Box>

                {dc !== undefined && (
                    <Typography variant="caption" color="text.secondary">
                        vs DC {dc}
                    </Typography>
                )}

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

                {success !== undefined && (
                    <Chip
                        label={success ? 'SUCCESS' : 'FAIL'}
                        size="small"
                        sx={{
                            height: 20,
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            bgcolor: success ? 'rgba(124, 231, 194, 0.2)' : 'rgba(255, 107, 107, 0.2)',
                            color: success ? '#7ce7c2' : '#ff6b6b',
                            ml: 0.5
                        }}
                    />
                )}

                {isCriticalSuccess && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [0, 1.3, 1] }}
                        transition={{ delay: 0.3, duration: 0.4 }}
                    >
                        <Typography sx={{ fontSize: '0.9rem' }}>✨</Typography>
                    </motion.div>
                )}

                {isCriticalFailure && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [0, 1.3, 1] }}
                        transition={{ delay: 0.3, duration: 0.4 }}
                    >
                        <Typography sx={{ fontSize: '0.9rem' }}>💀</Typography>
                    </motion.div>
                )}
            </Box>
        </motion.div>
    );
}
