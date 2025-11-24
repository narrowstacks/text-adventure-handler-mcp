import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, Typography, LinearProgress, Stack } from '@mui/material';
import { useReducedMotion } from '../utils/animations';

interface StatBarProps {
    name: string;
    value: number;
    maxValue?: number;
    icon?: React.ReactNode;
    color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
    showChange?: boolean;
}

export default function StatBar({
    name,
    value,
    maxValue = 20,
    icon,
    color = 'primary',
    showChange = true
}: StatBarProps) {
    const reducedMotion = useReducedMotion();
    const prevValueRef = useRef<number>(value);
    const [change, setChange] = useState<number | null>(null);

    useEffect(() => {
        if (showChange && prevValueRef.current !== value) {
            const diff = value - prevValueRef.current;
            setChange(diff);
            prevValueRef.current = value;

            // Clear change indicator after animation
            const timeout = setTimeout(() => setChange(null), 2000);
            return () => clearTimeout(timeout);
        }
    }, [value, showChange]);

    const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));
    const increased = change !== null && change > 0;

    return (
        <motion.div
            animate={
                reducedMotion || change === null
                    ? {}
                    : {
                          backgroundColor: increased
                              ? ['transparent', 'rgba(124, 231, 194, 0.15)', 'transparent']
                              : ['transparent', 'rgba(255, 107, 107, 0.15)', 'transparent']
                      }
            }
            transition={{ duration: 0.6 }}
            style={{ borderRadius: 8, padding: '4px 0' }}
        >
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {icon}
                    <Typography variant="body2" fontWeight={500}>
                        {name}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <AnimatePresence mode="wait">
                        <motion.span
                            key={value}
                            initial={reducedMotion ? {} : { y: increased ? 10 : -10, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: increased ? -10 : 10, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            style={{ fontWeight: 600, fontSize: '0.9rem' }}
                        >
                            {value}
                        </motion.span>
                    </AnimatePresence>
                    <Typography variant="caption" color="text.secondary">
                        / {maxValue}
                    </Typography>

                    <AnimatePresence>
                        {change !== null && (
                            <motion.span
                                initial={{ opacity: 0, x: -10, scale: 0.8 }}
                                animate={{ opacity: 1, x: 0, scale: 1 }}
                                exit={{ opacity: 0, x: 10, scale: 0.8 }}
                                transition={{ duration: 0.3 }}
                                style={{
                                    marginLeft: 4,
                                    fontSize: '0.75rem',
                                    fontWeight: 700,
                                    color: increased ? '#7ce7c2' : '#ff6b6b'
                                }}
                            >
                                {increased ? '+' : ''}
                                {change}
                            </motion.span>
                        )}
                    </AnimatePresence>
                </Box>
            </Stack>

            <motion.div
                animate={
                    reducedMotion || change === null
                        ? {}
                        : {
                              boxShadow: increased
                                  ? [
                                        '0 0 0px rgba(124, 231, 194, 0)',
                                        '0 0 10px rgba(124, 231, 194, 0.5)',
                                        '0 0 0px rgba(124, 231, 194, 0)'
                                    ]
                                  : [
                                        '0 0 0px rgba(255, 107, 107, 0)',
                                        '0 0 10px rgba(255, 107, 107, 0.5)',
                                        '0 0 0px rgba(255, 107, 107, 0)'
                                    ]
                          }
                }
                transition={{ duration: 0.6 }}
                style={{ borderRadius: 4 }}
            >
                <LinearProgress
                    variant="determinate"
                    value={percentage}
                    color={color}
                    sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'rgba(255,255,255,0.1)',
                        '& .MuiLinearProgress-bar': {
                            borderRadius: 3,
                            transition: 'transform 0.5s ease-in-out'
                        }
                    }}
                />
            </motion.div>
        </motion.div>
    );
}
