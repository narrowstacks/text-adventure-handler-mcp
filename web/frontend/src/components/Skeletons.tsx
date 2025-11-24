import { Skeleton, Card, CardContent, Stack, Box } from '@mui/material';

export function CardSkeleton() {
    return (
        <Card>
            <CardContent>
                <Skeleton variant="text" width="40%" height={28} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="rectangular" height={80} sx={{ mt: 2, borderRadius: 1 }} />
            </CardContent>
        </Card>
    );
}

export function SessionCardSkeleton() {
    return (
        <Card>
            <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                    <Skeleton variant="text" width="50%" height={28} />
                    <Skeleton variant="circular" width={24} height={24} />
                </Stack>
                <Skeleton variant="text" width="70%" />
                <Skeleton variant="rectangular" height={10} sx={{ mt: 2, borderRadius: 5 }} />
                <Stack direction="row" justifyContent="space-between" mt={2}>
                    <Skeleton variant="text" width="30%" />
                    <Skeleton variant="text" width="20%" />
                </Stack>
            </CardContent>
        </Card>
    );
}

export function HistoryEntrySkeleton({ count = 3 }: { count?: number }) {
    return (
        <Stack spacing={1.5}>
            {Array.from({ length: count }).map((_, i) => (
                <Box
                    key={i}
                    sx={{
                        p: 2,
                        borderRadius: 1,
                        bgcolor: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.05)'
                    }}
                >
                    <Stack direction="row" spacing={2} alignItems="flex-start">
                        <Skeleton variant="circular" width={32} height={32} />
                        <Box sx={{ flex: 1 }}>
                            <Skeleton variant="text" width="80%" />
                            <Skeleton variant="text" width="60%" />
                            <Skeleton variant="text" width="40%" sx={{ mt: 1 }} />
                        </Box>
                    </Stack>
                </Box>
            ))}
        </Stack>
    );
}

export function StatsSkeleton() {
    return (
        <Stack spacing={1.5}>
            {Array.from({ length: 4 }).map((_, i) => (
                <Box key={i}>
                    <Stack direction="row" justifyContent="space-between" mb={0.5}>
                        <Skeleton variant="text" width="30%" height={20} />
                        <Skeleton variant="text" width="15%" height={20} />
                    </Stack>
                    <Skeleton variant="rectangular" height={6} sx={{ borderRadius: 3 }} />
                </Box>
            ))}
        </Stack>
    );
}

export function InventorySkeleton() {
    return (
        <Stack spacing={1}>
            {Array.from({ length: 3 }).map((_, i) => (
                <Box
                    key={i}
                    sx={{
                        p: 1.5,
                        borderRadius: 1,
                        bgcolor: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.05)'
                    }}
                >
                    <Skeleton variant="text" width="60%" height={22} />
                    <Skeleton variant="text" width="80%" height={16} sx={{ mt: 0.5 }} />
                    <Stack direction="row" spacing={0.5} mt={1}>
                        <Skeleton variant="rectangular" width={60} height={22} sx={{ borderRadius: 11 }} />
                        <Skeleton variant="rectangular" width={50} height={22} sx={{ borderRadius: 11 }} />
                    </Stack>
                </Box>
            ))}
        </Stack>
    );
}

export function QuestSkeleton() {
    return (
        <Stack spacing={1.5}>
            {Array.from({ length: 2 }).map((_, i) => (
                <Box
                    key={i}
                    sx={{
                        p: 1.5,
                        borderRadius: 1,
                        bgcolor: 'rgba(255,255,255,0.03)'
                    }}
                >
                    <Skeleton variant="text" width="70%" height={24} />
                    <Skeleton variant="rectangular" height={4} sx={{ mt: 1, mb: 1.5, borderRadius: 2 }} />
                    <Stack spacing={0.5}>
                        <Stack direction="row" spacing={1} alignItems="center">
                            <Skeleton variant="circular" width={18} height={18} />
                            <Skeleton variant="text" width="60%" height={18} />
                        </Stack>
                        <Stack direction="row" spacing={1} alignItems="center">
                            <Skeleton variant="circular" width={18} height={18} />
                            <Skeleton variant="text" width="50%" height={18} />
                        </Stack>
                    </Stack>
                </Box>
            ))}
        </Stack>
    );
}

export default {
    CardSkeleton,
    SessionCardSkeleton,
    HistoryEntrySkeleton,
    StatsSkeleton,
    InventorySkeleton,
    QuestSkeleton
};
