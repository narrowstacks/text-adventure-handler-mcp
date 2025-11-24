import { motion } from 'framer-motion';
import { Box, Typography, Stack, Tooltip } from '@mui/material';
import { useReducedMotion } from '../utils/animations';
import FavoriteIcon from '@mui/icons-material/Favorite';
import HeartBrokenIcon from '@mui/icons-material/HeartBroken';

interface RelationshipGraphProps {
    relationships: Record<string, number>;
}

export default function RelationshipGraph({ relationships }: RelationshipGraphProps) {
    const reducedMotion = useReducedMotion();
    const entries = Object.entries(relationships).sort((a, b) => b[1] - a[1]);

    if (entries.length === 0) {
        return (
            <Typography variant="body2" color="text.secondary">
                No relationships established
            </Typography>
        );
    }

    return (
        <Stack spacing={1.5}>
            {entries.map(([name, value], index) => {
                // Normalize -100..100 to 0..100 for display
                const normalizedValue = ((value + 100) / 200) * 100;
                const isPositive = value >= 0;
                const isStrong = Math.abs(value) >= 50;

                const getLabel = () => {
                    if (value >= 75) return 'Allied';
                    if (value >= 25) return 'Friendly';
                    if (value >= -25) return 'Neutral';
                    if (value >= -75) return 'Hostile';
                    return 'Enemy';
                };

                const getColor = () => {
                    if (value >= 50) return '#7ce7c2';
                    if (value >= 0) return '#a8e6cf';
                    if (value >= -50) return '#ffb347';
                    return '#ff6b6b';
                };

                return (
                    <motion.div
                        key={name}
                        initial={reducedMotion ? {} : { opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                    >
                        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.5}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                {isPositive ? (
                                    <FavoriteIcon
                                        sx={{
                                            fontSize: 14,
                                            color: getColor(),
                                            opacity: isStrong ? 1 : 0.6
                                        }}
                                    />
                                ) : (
                                    <HeartBrokenIcon
                                        sx={{
                                            fontSize: 14,
                                            color: getColor(),
                                            opacity: isStrong ? 1 : 0.6
                                        }}
                                    />
                                )}
                                <Typography variant="body2" fontWeight={500}>
                                    {name}
                                </Typography>
                            </Box>
                            <Tooltip title={getLabel()} arrow>
                                <Typography
                                    variant="caption"
                                    fontWeight={600}
                                    sx={{ color: getColor() }}
                                >
                                    {value > 0 ? '+' : ''}
                                    {value}
                                </Typography>
                            </Tooltip>
                        </Stack>

                        <Box
                            sx={{
                                position: 'relative',
                                height: 8,
                                borderRadius: 4,
                                bgcolor: 'rgba(255, 107, 107, 0.2)',
                                overflow: 'hidden'
                            }}
                        >
                            {/* Positive fill (green, from center to right) */}
                            <motion.div
                                initial={reducedMotion ? {} : { width: '50%' }}
                                animate={{ width: `${normalizedValue}%` }}
                                transition={{ duration: 0.5, ease: 'easeOut' }}
                                style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    height: '100%',
                                    background: isPositive
                                        ? `linear-gradient(90deg, rgba(255, 107, 107, 0.3) 50%, ${getColor()} ${normalizedValue}%)`
                                        : `linear-gradient(90deg, ${getColor()} 0%, rgba(168, 230, 207, 0.3) 50%)`,
                                    borderRadius: 4
                                }}
                            />

                            {/* Center marker */}
                            <Box
                                sx={{
                                    position: 'absolute',
                                    left: '50%',
                                    top: 0,
                                    width: 2,
                                    height: '100%',
                                    bgcolor: 'rgba(255, 255, 255, 0.3)',
                                    transform: 'translateX(-50%)'
                                }}
                            />

                            {/* Current value marker */}
                            <motion.div
                                initial={reducedMotion ? {} : { left: '50%' }}
                                animate={{ left: `${normalizedValue}%` }}
                                transition={{ duration: 0.5, ease: 'easeOut' }}
                                style={{
                                    position: 'absolute',
                                    top: '50%',
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    backgroundColor: getColor(),
                                    border: '2px solid rgba(255,255,255,0.8)',
                                    transform: 'translate(-50%, -50%)',
                                    boxShadow: `0 0 10px ${getColor()}`
                                }}
                            />
                        </Box>
                    </motion.div>
                );
            })}
        </Stack>
    );
}
