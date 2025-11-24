import { Card, CardContent, Typography, Box } from '@mui/material';
import type { QuestStatus } from '../types';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';

interface QuestTrackerProps {
    quests: QuestStatus[];
}

export default function QuestTracker({ quests }: QuestTrackerProps) {
    if (!quests.length) return null;

    return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <EmojiEventsIcon color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Quest Log</Typography>
                </Box>
                {quests.map((quest) => (
                    <Box key={quest.id} sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                            {quest.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            {quest.description}
                        </Typography>
                        
                        {quest.objectives.map((obj, i) => {
                            const isCompleted = quest.completed_objectives.includes(obj);
                            return (
                                <Box key={i} sx={{ display: 'flex', alignItems: 'center', mt: 0.5, ml: 1 }}>
                                    {isCompleted ? 
                                        <CheckBoxIcon fontSize="small" color="success" sx={{ mr: 1 }} /> : 
                                        <CheckBoxOutlineBlankIcon fontSize="small" color="action" sx={{ mr: 1 }} />
                                    }
                                    <Typography variant="caption" sx={{ textDecoration: isCompleted ? 'line-through' : 'none' }}>
                                        {obj}
                                    </Typography>
                                </Box>
                            );
                        })}
                    </Box>
                ))}
            </CardContent>
        </Card>
    );
}