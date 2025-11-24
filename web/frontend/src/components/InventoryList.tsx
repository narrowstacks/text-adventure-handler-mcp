import { Card, CardContent, Typography, List, ListItem, ListItemText, Box } from '@mui/material';
import type { InventoryItem } from '../types';
import BackpackIcon from '@mui/icons-material/Backpack';

interface InventoryListProps {
    inventory: InventoryItem[];
}

export default function InventoryList({ inventory }: InventoryListProps) {
    if (!inventory.length) return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                 <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <BackpackIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Inventory</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">Empty</Typography>
            </CardContent>
        </Card>
    );

    return (
         <Card sx={{ mb: 2 }}>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <BackpackIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Inventory</Typography>
                </Box>
                <List dense>
                    {inventory.map((item, index) => (
                        <ListItem key={index} disablePadding sx={{ mb: 1 }}>
                            <ListItemText 
                                primary={`${item.name} ${item.quantity > 1 ? `(x${item.quantity})` : ''}`}
                                secondary={item.description}
                                primaryTypographyProps={{ fontWeight: 'medium' }}
                            />
                        </ListItem>
                    ))}
                </List>
            </CardContent>
        </Card>
    );
}