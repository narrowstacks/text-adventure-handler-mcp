import { Card, CardContent, Typography, Box, LinearProgress, Chip, Stack } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import type { QuestStatus } from '../types';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import { useReducedMotion } from '../utils/animations';
import { useQuestCompletion } from './Confetti';

interface QuestTrackerProps {
    quests: QuestStatus[];
}

export default function QuestTracker({ quests }: QuestTrackerProps) {
    const reducedMotion = useReducedMotion();

    // Trigger confetti when quests complete
    useQuestCompletion(quests);

    if (!quests.length) return null;

    const getProgress = (quest: QuestStatus) => {
        const total = quest.objectives.length;
        const completed = quest.completed_objectives.length;
        return total > 0 ? (completed / total) * 100 : 0;
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return '#7ce7c2';
            case 'failed':
                return '#ff6b6b';
            case 'active':
                return '#f0c75e';
            default:
                return 'text.secondary';
        }
    };

    return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <EmojiEventsIcon color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Quest Log</Typography>
                </Box>

                <AnimatePresence>
                    {quests.map((quest, qIndex) => {
                        const progress = getProgress(quest);
                        const isComplete = quest.status === 'completed';

                        return (
                            <motion.div
                                key={quest.id}
                                initial={reducedMotion ? {} : { opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ delay: qIndex * 0.05 }}
                            >
                                <Box
                                    sx={{
                                        mb: 2.5,
                                        p: 1.5,
                                        borderRadius: 1,
                                        bgcolor: 'rgba(255,255,255,0.03)',
                                        border: '1px solid',
                                        borderColor: isComplete
                                            ? 'rgba(124, 231, 194, 0.3)'
                                            : 'rgba(255,255,255,0.05)'
                                    }}
                                >
                                    <Stack
                                        direction="row"
                                        justifyContent="space-between"
                                        alignItems="center"
                                        mb={0.5}
                                    >
                                        <Typography variant="subtitle1" fontWeight="bold">
                                            {quest.title}
                                        </Typography>
                                        <Chip
                                            label={quest.status.toUpperCase()}
                                            size="small"
                                            sx={{
                                                height: 20,
                                                fontSize: '0.65rem',
                                                fontWeight: 700,
                                                bgcolor: `${getStatusColor(quest.status)}20`,
                                                color: getStatusColor(quest.status),
                                                border: `1px solid ${getStatusColor(quest.status)}40`
                                            }}
                                        />
                                    </Stack>

                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                                        {quest.description}
                                    </Typography>

                                    {/* Progress bar */}
                                    <Box sx={{ mb: 1.5 }}>
                                        <motion.div
                                            animate={
                                                reducedMotion
                                                    ? {}
                                                    : {
                                                          boxShadow:
                                                              progress === 100
                                                                  ? [
                                                                        '0 0 0px rgba(124, 231, 194, 0)',
                                                                        '0 0 15px rgba(124, 231, 194, 0.5)',
                                                                        '0 0 0px rgba(124, 231, 194, 0)'
                                                                    ]
                                                                  : 'none'
                                                      }
                                            }
                                            transition={{ duration: 1, repeat: progress === 100 ? 2 : 0 }}
                                            style={{ borderRadius: 4 }}
                                        >
                                            <LinearProgress
                                                variant="determinate"
                                                value={progress}
                                                sx={{
                                                    height: 6,
                                                    borderRadius: 3,
                                                    bgcolor: 'rgba(255,255,255,0.1)',
                                                    '& .MuiLinearProgress-bar': {
                                                        borderRadius: 3,
                                                        bgcolor: isComplete ? '#7ce7c2' : '#f0c75e',
                                                        transition: 'transform 0.5s ease-in-out'
                                                    }
                                                }}
                                            />
                                        </motion.div>
                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{ mt: 0.5, display: 'block' }}
                                        >
                                            {quest.completed_objectives.length} / {quest.objectives.length} objectives
                                        </Typography>
                                    </Box>

                                    {/* Objectives */}
                                    {quest.objectives.map((obj, i) => {
                                        const isObjCompleted = quest.completed_objectives.includes(obj);
                                        return (
                                            <motion.div
                                                key={i}
                                                initial={reducedMotion ? {} : { opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: i * 0.03 }}
                                            >
                                                <Box
                                                    sx={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        mt: 0.75,
                                                        ml: 0.5
                                                    }}
                                                >
                                                    <motion.div
                                                        animate={
                                                            isObjCompleted && !reducedMotion
                                                                ? { scale: [1, 1.3, 1] }
                                                                : {}
                                                        }
                                                        transition={{ duration: 0.3 }}
                                                    >
                                                        {isObjCompleted ? (
                                                            <CheckCircleIcon
                                                                sx={{
                                                                    fontSize: 18,
                                                                    color: '#7ce7c2',
                                                                    mr: 1
                                                                }}
                                                            />
                                                        ) : (
                                                            <RadioButtonUncheckedIcon
                                                                sx={{
                                                                    fontSize: 18,
                                                                    color: 'text.disabled',
                                                                    mr: 1
                                                                }}
                                                            />
                                                        )}
                                                    </motion.div>
                                                    <Typography
                                                        variant="body2"
                                                        sx={{
                                                            textDecoration: isObjCompleted
                                                                ? 'line-through'
                                                                : 'none',
                                                            color: isObjCompleted
                                                                ? 'text.secondary'
                                                                : 'text.primary',
                                                            opacity: isObjCompleted ? 0.7 : 1
                                                        }}
                                                    >
                                                        {obj}
                                                    </Typography>
                                                </Box>
                                            </motion.div>
                                        );
                                    })}
                                </Box>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </CardContent>
        </Card>
    );
}